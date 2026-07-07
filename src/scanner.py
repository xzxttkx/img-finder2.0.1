"""File system scanner for image files."""

import os
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ImageFile:
    """Represents a single image file with its metadata and computed hashes."""
    path: str
    file_size: int
    modified_time: float
    md5_hash: str = ""
    dhash: str = ""


class ImageScanner:
    """Recursively scans directories for image files."""

    SUPPORTED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.webp', '.heic', '.heif', '.tiff', '.tif'
    }

    # Directories to skip during scanning
    SKIP_DIRS = {
        '.thumbnails', '.Trash', 'thumbnails', 'cache',
        '.cache', 'temp', '.temp', 'tmp', '.tmp'
    }

    def __init__(self):
        self._cancelled = False

    def cancel(self):
        """Signal the scanner to stop scanning."""
        self._cancelled = True

    def scan(
        self,
        root_path: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> list[ImageFile]:
        """
        Recursively scan a directory for image files.

        Args:
            root_path: The root directory to start scanning from.
            progress_callback: Called with (files_found, current_path) for UI updates.

        Returns:
            List of ImageFile objects sorted by path.
        """
        self._cancelled = False
        images: list[ImageFile] = []

        for dirpath, dirnames, filenames in os.walk(root_path):
            if self._cancelled:
                break

            # Filter out directories to skip
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in self.SKIP_DIRS
                and not d.startswith('.')
            ]

            for filename in filenames:
                if self._cancelled:
                    break

                ext = os.path.splitext(filename)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue

                filepath = os.path.join(dirpath, filename)
                try:
                    stat = os.stat(filepath)
                    images.append(ImageFile(
                        path=filepath,
                        file_size=stat.st_size,
                        modified_time=stat.st_mtime
                    ))
                except OSError:
                    # Skip files we can't access
                    continue

                if progress_callback and len(images) % 50 == 0:
                    progress_callback(len(images), filepath)

        if progress_callback:
            progress_callback(len(images), "")

        images.sort(key=lambda img: img.path)
        return images

    def count_images(self, root_path: str) -> int:
        """Quick count of image files without building the full list."""
        count = 0
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in self.SKIP_DIRS
                and not d.startswith('.')
            ]
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.SUPPORTED_EXTENSIONS:
                    count += 1
        return count
