"""Duplicate detection core logic. Groups images by exact (MD5) and perceptual (dHash) similarity."""

from dataclasses import dataclass, field
from typing import Callable, Optional

from .scanner import ImageFile
from .hasher import HashEngine
from .db import ScanCache


@dataclass
class DuplicateGroup:
    """A group of duplicate or similar images."""
    group_id: int
    images: list[ImageFile]
    duplicate_type: str  # "exact" or "similar"
    total_wasted_size: int = 0  # Bytes that can be freed (all except largest/smallest)

    def __post_init__(self):
        if not self.total_wasted_size and len(self.images) > 1:
            # Keep the largest file, wasted = sum of the rest
            sorted_imgs = sorted(self.images, key=lambda x: x.file_size, reverse=True)
            self.total_wasted_size = sum(img.file_size for img in sorted_imgs[1:])


@dataclass
class DuplicateReport:
    """Complete scan report containing all duplicate groups and statistics."""
    scan_time: str
    total_images: int
    total_duplicate_groups: int
    exact_groups: list[DuplicateGroup]
    similar_groups: list[DuplicateGroup]
    total_wasted_bytes: int
    root_path: str

    @property
    def all_groups(self) -> list[DuplicateGroup]:
        return self.exact_groups + self.similar_groups

    @property
    def total_wasted_mb(self) -> float:
        return round(self.total_wasted_bytes / (1024 * 1024), 2)


class DuplicateDetector:
    """
    Detects duplicate images using a two-phase approach:
    Phase 1: Group by MD5 (exact duplicates)
    Phase 2: Group by dHash Hamming distance (visual/perceptual duplicates)
    """

    # Default threshold for dHash Hamming distance
    DEFAULT_SIMILARITY_THRESHOLD = 10

    def __init__(self, cache: Optional[ScanCache] = None):
        """
        Args:
            cache: Optional ScanCache instance for reusing previous hash results.
        """
        self.cache = cache
        self._cancelled = False

    def cancel(self):
        """Cancel the current detection process."""
        self._cancelled = True

    def detect(
        self,
        images: list[ImageFile],
        threshold: int = DEFAULT_SIMILARITY_THRESHOLD,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> DuplicateReport:
        """
        Run duplicate detection on a list of image files.

        Args:
            images: List of ImageFile objects from the scanner.
            threshold: Hamming distance threshold for perceptual similarity (0-64).
                       Lower = stricter matching. Default 10.
            on_progress: Callback for UI updates: (phase, current, total)

        Returns:
            DuplicateReport with all detected duplicate groups and statistics.
        """
        self._cancelled = False
        total = len(images)

        # Phase 1: Compute hashes (with cache support)
        self._compute_hashes(images, on_progress, total)
        if self._cancelled:
            return self._empty_report(images)

        # Phase 2: Find exact duplicates by MD5
        if on_progress:
            on_progress("检测精确重复...", 0, total)
        exact_groups = self._find_exact_duplicates(images)
        if self._cancelled:
            return self._empty_report(images)

        # Phase 3: Find perceptual duplicates by dHash
        # Exclude images already in exact duplicate groups from similar detection
        exact_paths: set[str] = set()
        for g in exact_groups:
            for img in g.images:
                exact_paths.add(img.path)

        remaining_images = [img for img in images if img.path not in exact_paths]

        if on_progress:
            on_progress("检测相似图片...", 0, len(remaining_images))
        similar_groups = self._find_similar_duplicates(remaining_images, threshold, on_progress)

        # Build report
        all_groups = exact_groups + similar_groups
        total_wasted = sum(g.total_wasted_size for g in all_groups)

        from datetime import datetime
        return DuplicateReport(
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_images=total,
            total_duplicate_groups=len(all_groups),
            exact_groups=exact_groups,
            similar_groups=similar_groups,
            total_wasted_bytes=total_wasted,
            root_path=""
        )

    def _compute_hashes(
        self,
        images: list[ImageFile],
        on_progress: Optional[Callable[[str, int, int], None]],
        total: int
    ):
        """Compute MD5 and dHash for all images, using cache when available."""
        engine = HashEngine()

        for i, img in enumerate(images):
            if self._cancelled:
                break

            # Check cache first
            if self.cache and not self.cache.is_stale(img.path, img.modified_time):
                cached = self.cache.get_cached(img.path)
                if cached:
                    img.md5_hash = cached['md5']
                    img.dhash = cached['dhash']

            # Compute MD5 if needed
            if not img.md5_hash:
                if on_progress:
                    on_progress(f"计算MD5: {i+1}/{total}", i + 1, total)
                img.md5_hash = engine.md5_hash(img.path)

            # Compute dHash if needed (skip if we already have it)
            if not img.dhash:
                if on_progress:
                    on_progress(f"计算感知哈希: {i+1}/{total}", i + 1, total)
                img.dhash = engine.dhash(img.path)

            # Save to cache
            if self.cache and img.md5_hash and img.dhash:
                self.cache.upsert(
                    img.path, img.file_size, img.modified_time,
                    img.md5_hash, img.dhash
                )

    def _find_exact_duplicates(self, images: list[ImageFile]) -> list[DuplicateGroup]:
        """Group images by identical MD5 hash."""
        md5_map: dict[str, list[ImageFile]] = {}
        for img in images:
            if not img.md5_hash:
                continue
            if img.md5_hash not in md5_map:
                md5_map[img.md5_hash] = []
            md5_map[img.md5_hash].append(img)

        groups = []
        group_id = 0
        for imgs in md5_map.values():
            if len(imgs) > 1:
                groups.append(DuplicateGroup(
                    group_id=group_id,
                    images=imgs,
                    duplicate_type="exact"
                ))
                group_id += 1

        return groups

    def _find_similar_duplicates(
        self,
        images: list[ImageFile],
        threshold: int,
        on_progress: Optional[Callable[[str, int, int], None]]
    ) -> list[DuplicateGroup]:
        """
        Group images by perceptual similarity (dHash Hamming distance).
        Two-phase approach:
        1. Same dHash → same group (fast, O(n))
        2. Nearby dHash (Hamming ≤ threshold) → merge groups via union-find
        """
        engine = HashEngine()

        if len(images) < 2:
            return []

        # Build dHash → images map (all images with valid dHash)
        dhash_map: dict[str, list[ImageFile]] = {}
        for img in images:
            if not img.dhash:
                continue
            if img.dhash not in dhash_map:
                dhash_map[img.dhash] = []
            dhash_map[img.dhash].append(img)

        if len(dhash_map) < 2 and all(len(v) <= 1 for v in dhash_map.values()):
            return []  # No possible similar groups

        # Phase 1: Group by identical dHash
        # These are images whose dHash bits are exactly the same — very likely visually identical
        same_hash_groups: list[list[ImageFile]] = [
            imgs for imgs in dhash_map.values() if len(imgs) > 1
        ]

        # Track which dHash values are already in a same-hash group
        grouped_hashes: set[str] = set()
        for imgs in same_hash_groups:
            grouped_hashes.add(imgs[0].dhash)

        # Phase 2: Compare remaining unique hashes for near-similarity
        remaining_hashes = [h for h in dhash_map.keys() if h not in grouped_hashes]

        if len(remaining_hashes) >= 2:
            similar_pairs: list[tuple[str, str]] = []

            for i in range(len(remaining_hashes)):
                if self._cancelled:
                    return []
                h1 = remaining_hashes[i]
                for j in range(i + 1, len(remaining_hashes)):
                    h2 = remaining_hashes[j]
                    dist = engine.hamming_distance(h1, h2)
                    if 0 < dist <= threshold:
                        similar_pairs.append((h1, h2))

            # Union-find to merge connected components
            if similar_pairs:
                parent: dict[str, str] = {}

                def find(x):
                    if x not in parent:
                        parent[x] = x
                    if parent[x] != x:
                        parent[x] = find(parent[x])
                    return parent[x]

                def union(x, y):
                    px, py = find(x), find(y)
                    if px != py:
                        parent[px] = py

                for h1, h2 in similar_pairs:
                    union(h1, h2)
                    # Also init parent for already-grouped hashes that may connect
                    for h in (h1, h2):
                        if h not in parent:
                            parent[h] = h

                # Collect images per union-find component (remaining hashes only)
                component_images: dict[str, list[ImageFile]] = {}
                for h in remaining_hashes:
                    root = find(h)
                    if root not in component_images:
                        component_images[root] = []
                    component_images[root].extend(dhash_map.get(h, []))

                for imgs in component_images.values():
                    if len(imgs) > 1:
                        same_hash_groups.append(imgs)

        # Convert to DuplicateGroup objects
        result = []
        group_id = 1000  # Offset to distinguish from exact groups
        seen_paths: set[str] = set()

        for imgs in same_hash_groups:
            # Deduplicate by path and skip images already in exact groups
            deduped = []
            for img in imgs:
                if img.path not in seen_paths:
                    seen_paths.add(img.path)
                    deduped.append(img)

            if len(deduped) > 1:
                result.append(DuplicateGroup(
                    group_id=group_id,
                    images=deduped,
                    duplicate_type="similar"
                ))
                group_id += 1

        return result

    def _empty_report(self, images: list[ImageFile]) -> DuplicateReport:
        from datetime import datetime
        return DuplicateReport(
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_images=len(images),
            total_duplicate_groups=0,
            exact_groups=[],
            similar_groups=[],
            total_wasted_bytes=0,
            root_path=""
        )
