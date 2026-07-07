"""Hash computation engine: MD5 for exact duplicates, dHash for perceptual duplicates."""

import hashlib
from PIL import Image


class HashEngine:
    """Computes MD5 and perceptual (dHash) hashes for image files."""

    # Buffer size for MD5 chunked reading (8KB)
    MD5_CHUNK_SIZE = 8192

    @staticmethod
    def md5_hash(file_path: str) -> str:
        """
        Compute the MD5 hash of a file's contents.
        Reads the file in chunks to handle large files efficiently.

        Args:
            file_path: Absolute path to the file.

        Returns:
            Hexadecimal MD5 digest string, or empty string on error.
        """
        md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(HashEngine.MD5_CHUNK_SIZE)
                    if not chunk:
                        break
                    md5.update(chunk)
            return md5.hexdigest()
        except (IOError, OSError):
            return ""

    @staticmethod
    def dhash(file_path: str, hash_size: int = 8) -> str:
        """
        Compute the difference hash (dHash) for perceptual image comparison.

        Algorithm:
        1. Open image and convert to grayscale.
        2. Resize to (hash_size+1) × hash_size pixels (9×8 for 64-bit hash).
        3. For each row, compare adjacent pixels: left < right → 1, else 0.
        4. Pack bits into a hexadecimal string.

        Args:
            file_path: Absolute path to the image file.
            hash_size: Size of the hash grid (default 8 → 64-bit hash).

        Returns:
            Hexadecimal dHash string, or empty string on error.
        """
        try:
            img = Image.open(file_path)
            img = img.convert('L')  # Grayscale
            img = img.resize((hash_size + 1, hash_size), Image.LANCZOS)

            pixels = list(img.getdata())
            width = hash_size + 1

            hash_bits = []
            for row in range(hash_size):
                row_start = row * width
                for col in range(hash_size):
                    left = pixels[row_start + col]
                    right = pixels[row_start + col + 1]
                    hash_bits.append('1' if left < right else '0')

            # Convert binary string to hex
            hash_str = ''.join(hash_bits)
            hex_hash = hex(int(hash_str, 2))[2:].zfill(hash_size * hash_size // 4)
            return hex_hash

        except (IOError, OSError, ValueError):
            return ""

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        Compute the Hamming distance between two hexadecimal hash strings.

        Args:
            hash1: First hex hash string.
            hash2: Second hex hash string.

        Returns:
            Number of differing bits, or -1 if hashes have different lengths.
        """
        if not hash1 or not hash2:
            return -1
        if len(hash1) != len(hash2):
            return -1

        # Convert hex to int and XOR
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        xor = int1 ^ int2

        # Count set bits (Hamming distance)
        return xor.bit_count()
