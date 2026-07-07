"""SQLite cache layer for scan results. Avoids recomputing hashes on rescans."""

import os
import sqlite3
import threading
from datetime import datetime
from typing import Optional


class ScanCache:
    """
    Persists file hash results so that unchanged files don't need
    to be re-hashed on subsequent scans.
    """

    DB_FILENAME = "scan_cache.db"

    def __init__(self, storage_dir: str):
        """
        Args:
            storage_dir: Directory where the cache database will be stored
                         (typically the app's private data directory).
        """
        self.db_path = os.path.join(storage_dir, self.DB_FILENAME)
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        """Thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self):
        """Create the schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                path TEXT PRIMARY KEY,
                file_size INTEGER NOT NULL,
                mtime REAL NOT NULL,
                md5 TEXT NOT NULL DEFAULT '',
                dhash TEXT NOT NULL DEFAULT '',
                last_scan_time TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_md5 ON file_hashes(md5)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dhash ON file_hashes(dhash)
        """)
        conn.commit()
        conn.close()

    def get_cached(self, path: str) -> Optional[dict]:
        """Get cached hash data for a file, or None if not cached/stale."""
        try:
            row = self._conn.execute(
                "SELECT file_size, mtime, md5, dhash FROM file_hashes WHERE path = ?",
                (path,)
            ).fetchone()
            if row is None:
                return None
            return {
                'file_size': row[0],
                'mtime': row[1],
                'md5': row[2],
                'dhash': row[3],
            }
        except sqlite3.Error:
            return None

    def is_stale(self, path: str, current_mtime: float) -> bool:
        """Check if the cached entry for a file is stale (mtime changed)."""
        cached = self.get_cached(path)
        if cached is None:
            return True
        return abs(cached['mtime'] - current_mtime) > 0.001

    def upsert(self, path: str, file_size: int, mtime: float,
               md5: str, dhash: str):
        """Insert or update a cache entry for a file."""
        now = datetime.now().isoformat()
        try:
            self._conn.execute(
                """INSERT OR REPLACE INTO file_hashes
                   (path, file_size, mtime, md5, dhash, last_scan_time)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (path, file_size, mtime, md5, dhash, now)
            )
            self._conn.commit()
        except sqlite3.Error:
            pass

    def get_all_md5_groups(self) -> dict[str, list[str]]:
        """
        Get all files grouped by MD5 hash from cache.
        Returns {md5: [path1, path2, ...]} for hashes with >1 file.
        """
        try:
            rows = self._conn.execute(
                "SELECT md5, path FROM file_hashes WHERE md5 != '' ORDER BY md5"
            ).fetchall()
        except sqlite3.Error:
            return {}

        groups: dict[str, list[str]] = {}
        for md5, path in rows:
            if md5 not in groups:
                groups[md5] = []
            groups[md5].append(path)
        return {k: v for k, v in groups.items() if len(v) > 1}

    def clean_orphaned(self, existing_paths: set):
        """Remove cache entries for files that no longer exist."""
        try:
            rows = self._conn.execute("SELECT path FROM file_hashes").fetchall()
            to_delete = [row[0] for row in rows if row[0] not in existing_paths]
            if to_delete:
                self._conn.executemany(
                    "DELETE FROM file_hashes WHERE path = ?",
                    [(p,) for p in to_delete]
                )
                self._conn.commit()
        except sqlite3.Error:
            pass

    def close(self):
        """Close the thread-local database connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
