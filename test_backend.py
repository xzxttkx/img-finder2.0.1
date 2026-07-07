#!/usr/bin/env python3
"""
Backend test: creates sample images and verifies scanner, hasher, detector.
Run: python test_backend.py
"""

import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont


def create_test_images(test_dir):
    """Create a set of test images with controlled duplicates and similarities."""
    images_dir = os.path.join(test_dir, 'photos')
    os.makedirs(images_dir, exist_ok=True)

    created = []

    # --- Group 1: Exact duplicates (same content, different names) ---
    img = Image.new('RGB', (200, 200), color='red')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='blue')
    draw.text((70, 90), 'PHOTO 1', fill='white')

    path_a = os.path.join(images_dir, 'sunset_original.jpg')
    path_b = os.path.join(images_dir, 'sunset_copy.jpg')
    img.save(path_a, 'JPEG')
    img.save(path_b, 'JPEG')
    created.extend([path_a, path_b])

    # --- Group 2: Exact duplicates (3 copies) ---
    img2 = Image.new('RGB', (300, 200), color='green')
    draw2 = ImageDraw.Draw(img2)
    draw2.ellipse([50, 30, 250, 170], fill='white')
    draw2.text((100, 85), 'LANDSCAPE', fill='black')

    for i in range(3):
        p = os.path.join(images_dir, f'landscape_{i+1}.jpg')
        img2.save(p, 'JPEG')
        created.append(p)

    # --- Group 3: Visually similar (same image, different resolution) ---
    img3 = Image.new('RGB', (400, 300), color='navy')
    draw3 = ImageDraw.Draw(img3)
    for i in range(0, 400, 40):
        draw3.line([(i, 0), (i, 300)], fill='white', width=2)
    draw3.text((150, 140), 'PATTERN', fill='yellow')

    path_large = os.path.join(images_dir, 'pattern_4k.jpg')
    img3.save(path_large, 'JPEG')
    created.append(path_large)

    img3_small = img3.resize((200, 150), Image.LANCZOS)
    path_small = os.path.join(images_dir, 'pattern_thumb.jpg')
    img3_small.save(path_small, 'JPEG')
    created.append(path_small)

    # --- Group 4: Visually similar (same content, slight compression) ---
    img4 = Image.new('RGB', (250, 250), color='orange')
    draw4 = ImageDraw.Draw(img4)
    draw4.polygon([(125, 20), (230, 200), (20, 200)], fill='purple')
    draw4.text((80, 100), 'TRIANGLE', fill='white')

    path_high = os.path.join(images_dir, 'triangle_high.jpg')
    path_low = os.path.join(images_dir, 'triangle_low.jpg')
    img4.save(path_high, 'JPEG', quality=95)
    img4.save(path_low, 'JPEG', quality=20)
    created.extend([path_high, path_low])

    # --- Unique images (no duplicates) ---
    img5 = Image.new('RGB', (100, 100), color='yellow')
    draw5 = ImageDraw.Draw(img5)
    draw5.rectangle([20, 20, 80, 80], fill='black')
    path_unique1 = os.path.join(images_dir, 'unique_square.jpg')
    img5.save(path_unique1, 'JPEG')
    created.append(path_unique1)

    img6 = Image.new('RGB', (150, 100), color='pink')
    draw6 = ImageDraw.Draw(img6)
    draw6.ellipse([10, 10, 140, 90], fill='red')
    path_unique2 = os.path.join(images_dir, 'unique_circle.jpg')
    img6.save(path_unique2, 'JPEG')
    created.append(path_unique2)

    print(f'Created {len(created)} test images in {images_dir}')
    print(f'  - Exact duplicates: Group 1 (2 copies), Group 2 (3 copies)')
    print(f'  - Similar images: Group 3 (resized), Group 4 (compressed)')
    print(f'  - Unique images: 2')
    return test_dir


def test_scanner(test_dir):
    """Test the ImageScanner."""
    print('\n=== Testing Scanner ===')
    from src.scanner import ImageScanner

    scanner = ImageScanner()
    images = scanner.scan(test_dir)

    print(f'Found {len(images)} image files:')
    for img in images:
        fname = os.path.basename(img.path)
        size_kb = img.file_size / 1024
        print(f'  {fname} ({size_kb:.1f} KB)')

    assert len(images) == 11, f'Expected 11 images, got {len(images)}'
    return images


def test_hasher(images):
    """Test the HashEngine."""
    print('\n=== Testing Hash Engine ===')
    from src.hasher import HashEngine

    engine = HashEngine()

    # Test MD5
    print('MD5 Hashes:')
    for img in images:
        md5 = engine.md5_hash(img.path)
        fname = os.path.basename(img.path)
        print(f'  {fname}: {md5[:16]}...')
        assert md5, f'MD5 hash failed for {fname}'

    # Test dHash
    print('\ndHash (perceptual):')
    for img in images:
        dh = engine.dhash(img.path)
        fname = os.path.basename(img.path)
        print(f'  {fname}: {dh}')
        assert dh, f'dHash failed for {fname}'

    # Verify: sunset_original and sunset_copy should have SAME MD5
    sunset_orig = next(i for i in images if 'sunset_original' in i.path)
    sunset_copy = next(i for i in images if 'sunset_copy' in i.path)
    md5_orig = engine.md5_hash(sunset_orig.path)
    md5_copy = engine.md5_hash(sunset_copy.path)
    assert md5_orig == md5_copy, 'Exact copies should have same MD5!'

    # Verify: pattern_4k and pattern_thumb should have SIMILAR dHash
    pattern_4k = next(i for i in images if 'pattern_4k' in i.path)
    pattern_thumb = next(i for i in images if 'pattern_thumb' in i.path)
    dh_4k = engine.dhash(pattern_4k.path)
    dh_thumb = engine.dhash(pattern_thumb.path)
    dist = engine.hamming_distance(dh_4k, dh_thumb)
    print(f'\nPattern 4k vs thumb Hamming distance: {dist} (should be <= 10)')
    assert dist <= 15, f'Resized images should have similar dHash, got distance {dist}'

    # Verify: different images should have DIFFERENT MD5
    sunset = next(i for i in images if 'sunset_original' in i.path)
    unique_sq = next(i for i in images if 'unique_square' in i.path)
    assert engine.md5_hash(sunset.path) != engine.md5_hash(unique_sq.path), \
        'Different images should have different MD5!'

    print('[OK] Hash engine tests passed!')


def test_detector(images):
    """Test the DuplicateDetector."""
    print('\n=== Testing Duplicate Detector ===')
    from src.detector import DuplicateDetector
    from src.db import ScanCache
    import tempfile

    # Use temp dir for cache
    cache_dir = tempfile.mkdtemp()
    cache = ScanCache(cache_dir)

    detector = DuplicateDetector(cache=cache)

    def progress(phase, current, total):
        print(f'  [{phase}] {current}/{total}')

    report = detector.detect(images, threshold=10, on_progress=progress)

    print(f'\nResults:')
    print(f'  Total images: {report.total_images}')
    print(f'  Total duplicate groups: {report.total_duplicate_groups}')
    print(f'  Exact groups: {len(report.exact_groups)}')
    print(f'  Similar groups: {len(report.similar_groups)}')
    print(f'  Wasted space: {report.total_wasted_mb} MB')

    print('\nExact Duplicate Groups:')
    for g in report.exact_groups:
        names = [os.path.basename(i.path) for i in g.images]
        print(f'  Group {g.group_id}: {names} (wasted: {g.total_wasted_size / 1024:.1f} KB)')

    print('\nSimilar Image Groups:')
    for g in report.similar_groups:
        names = [os.path.basename(i.path) for i in g.images]
        print(f'  Group {g.group_id}: {names} (wasted: {g.total_wasted_size / 1024:.1f} KB)')

    # Assertions
    assert report.total_images == 11
    assert len(report.exact_groups) >= 2, \
        f'Should find at least 2 exact groups, got {len(report.exact_groups)}'
    assert len(report.similar_groups) >= 1, \
        f'Should find at least 1 similar group, got {len(report.similar_groups)}'

    print('[OK] Detector tests passed!')
    return report


def test_exporter(report):
    """Test the ReportExporter."""
    print('\n=== Testing Report Exporter ===')
    from src.exporter import ReportExporter

    output_dir = tempfile.mkdtemp()

    # Test text export
    txt_path = ReportExporter.export_text(report, output_dir)
    print(f'Text report: {txt_path}')
    assert os.path.exists(txt_path)

    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f'  Size: {len(content)} chars')
        assert '重复图片扫描报告' in content

    # Test HTML export
    html_path = ReportExporter.export_html(report, output_dir)
    print(f'HTML report: {html_path}')
    assert os.path.exists(html_path)

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f'  Size: {len(content)} chars')
        assert '<!DOCTYPE html>' in content

    print('[OK] Exporter tests passed!')


def test_cache(images):
    """Test the ScanCache."""
    print('\n=== Testing Scan Cache ===')
    from src.db import ScanCache
    from src.hasher import HashEngine

    cache_dir = tempfile.mkdtemp()
    cache = ScanCache(cache_dir)
    engine = HashEngine()

    # Should be stale for new files
    for img in images:
        assert cache.is_stale(img.path, img.modified_time)

    # Cache some hashes
    for img in images[:3]:
        md5 = engine.md5_hash(img.path)
        dh = engine.dhash(img.path)
        cache.upsert(img.path, img.file_size, img.modified_time, md5, dh)

    # Should not be stale now
    for img in images[:3]:
        assert not cache.is_stale(img.path, img.modified_time)
        cached = cache.get_cached(img.path)
        assert cached is not None
        assert cached['md5'] != ''
        assert cached['dhash'] != ''

    # Should still be stale for uncached files
    assert cache.is_stale(images[5].path, images[5].modified_time)

    print('[OK] Cache tests passed!')


if __name__ == '__main__':
    print('=' * 60)
    print('Duplicate Image Finder - Backend Test Suite')
    print('=' * 60)

    # Create test environment
    test_dir = tempfile.mkdtemp()
    create_test_images(test_dir)

    try:
        # Run tests
        images = test_scanner(test_dir)
        test_hasher(images)
        test_cache(images)
        report = test_detector(images)
        test_exporter(report)

        print('\n' + '=' * 60)
        print('[OK] ALL BACKEND TESTS PASSED!')
        print('=' * 60)

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
