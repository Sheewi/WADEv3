# -*- coding: utf-8 -*-
"""
WADE Backup Manager
Automated backup and recovery system.
"""

import os
import shutil
import tarfile
import json
import time
import threading
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sqlite3


class BackupManager:
    """
    Comprehensive backup and recovery system for WADE.
    Handles configuration, data, logs, and system state backups.
    """

    def __init__(self, config: Dict = None):
        """Initialize the backup manager."""
        self.config = config or self._default_config()
        self.backup_thread = None
        self.running = False
        self.backup_db_path = os.path.join(
            self.config["backup_dir"], "backup_metadata.db"
        )

        # Ensure backup directories exist
        self._ensure_directories()

        # Initialize backup database
        self._init_backup_db()

    def _default_config(self) -> Dict:
        """Get default backup configuration."""
        return {
            "backup_dir": "/var/backups/wade",
            "retention_policy": {
                "daily": 7,  # Keep 7 daily backups
                "weekly": 4,  # Keep 4 weekly backups
                "monthly": 12,  # Keep 12 monthly backups
            },
            "compression": True,
            "encryption": False,
            "encryption_key": None,
            "schedule": {
                "enabled": True,
                "daily_time": "02:00",  # 2 AM
                "weekly_day": "sunday",
                "monthly_day": 1,
            },
            "backup_targets": {
                "config": {"path": "/etc/wade", "enabled": True, "priority": "high"},
                "data": {"path": "/var/lib/wade", "enabled": True, "priority": "high"},
                "logs": {
                    "path": "/var/log/wade",
                    "enabled": True,
                    "priority": "medium",
                },
                "certificates": {
                    "path": "/etc/wade/certs",
                    "enabled": True,
                    "priority": "critical",
                },
            },
            "remote_backup": {
                "enabled": False,
                "type": "s3",  # s3, ftp, rsync
                "config": {},
            },
        }

    def _ensure_directories(self):
        """Ensure backup directories exist."""
        backup_dir = self.config["backup_dir"]
        subdirs = ["daily", "weekly", "monthly", "temp", "restore"]

        for subdir in [backup_dir] + [os.path.join(backup_dir, d) for d in subdirs]:
            os.makedirs(subdir, mode=0o750, exist_ok=True)

    def _init_backup_db(self):
        """Initialize backup metadata database."""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS backups (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        backup_id TEXT UNIQUE NOT NULL,
                        backup_type TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        checksum TEXT,
                        targets TEXT,
                        status TEXT DEFAULT 'completed',
                        metadata TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS restore_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        restore_id TEXT UNIQUE NOT NULL,
                        backup_id TEXT NOT NULL,
                        restored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        restored_targets TEXT,
                        status TEXT,
                        notes TEXT,
                        FOREIGN KEY (backup_id) REFERENCES backups (backup_id)
                    )
                """
                )

                conn.commit()

        except Exception as e:
            print(f"Error initializing backup database: {e}")

    def create_backup(
        self, backup_type: str = "manual", targets: List[str] = None
    ) -> Optional[str]:
        """
        Create a backup.

        Args:
            backup_type: Type of backup (manual, daily, weekly, monthly)
            targets: List of targets to backup (None for all enabled)

        Returns:
            Backup ID if successful, None otherwise
        """
        try:
            # Generate backup ID
            backup_id = f"wade_{backup_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Determine targets
            if targets is None:
                targets = [
                    name
                    for name, config in self.config["backup_targets"].items()
                    if config.get("enabled", True)
                ]

            # Create backup directory
            backup_subdir = os.path.join(self.config["backup_dir"], backup_type)
            backup_file = os.path.join(backup_subdir, f"{backup_id}.tar")

            if self.config["compression"]:
                backup_file += ".gz"

            # Create backup archive
            success = self._create_archive(backup_file, targets)

            if success:
                # Calculate checksum
                checksum = self._calculate_checksum(backup_file)
                file_size = os.path.getsize(backup_file)

                # Store metadata
                self._store_backup_metadata(
                    backup_id, backup_type, backup_file, file_size, checksum, targets
                )

                # Clean up old backups
                self._cleanup_old_backups(backup_type)

                return backup_id

        except Exception as e:
            print(f"Error creating backup: {e}")

        return None

    def _create_archive(self, backup_file: str, targets: List[str]) -> bool:
        """Create backup archive."""
        try:
            mode = "w:gz" if self.config["compression"] else "w"

            with tarfile.open(backup_file, mode) as tar:
                for target in targets:
                    target_config = self.config["backup_targets"].get(target)
                    if not target_config:
                        continue

                    target_path = target_config["path"]
                    if os.path.exists(target_path):
                        # Add to archive with target name as arcname
                        tar.add(target_path, arcname=target)
                        print(f"Added {target_path} to backup")
                    else:
                        print(f"Warning: Target path {target_path} does not exist")

            return True

        except Exception as e:
            print(f"Error creating archive: {e}")
            return False

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _store_backup_metadata(
        self,
        backup_id: str,
        backup_type: str,
        file_path: str,
        file_size: int,
        checksum: str,
        targets: List[str],
    ):
        """Store backup metadata in database."""
        try:
            metadata = {
                "compression": self.config["compression"],
                "encryption": self.config["encryption"],
                "created_by": "wade_backup_manager",
                "version": "1.0",
            }

            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO backups
                    (backup_id, backup_type, file_path, file_size, checksum, targets, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        backup_id,
                        backup_type,
                        file_path,
                        file_size,
                        checksum,
                        json.dumps(targets),
                        json.dumps(metadata),
                    ),
                )
                conn.commit()

        except Exception as e:
            print(f"Error storing backup metadata: {e}")

    def _cleanup_old_backups(self, backup_type: str):
        """Clean up old backups based on retention policy."""
        try:
            retention = self.config["retention_policy"].get(backup_type, 7)
            backup_dir = os.path.join(self.config["backup_dir"], backup_type)

            # Get list of backup files
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith("wade_") and (
                    file.endswith(".tar") or file.endswith(".tar.gz")
                ):
                    file_path = os.path.join(backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))

            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)

            # Remove old backups
            for file_path, _ in backup_files[retention:]:
                os.remove(file_path)
                print(f"Removed old backup: {file_path}")

                # Remove from database
                backup_id = (
                    os.path.basename(file_path)
                    .replace(".tar.gz", "")
                    .replace(".tar", "")
                )
                self._remove_backup_metadata(backup_id)

        except Exception as e:
            print(f"Error cleaning up old backups: {e}")

    def _remove_backup_metadata(self, backup_id: str):
        """Remove backup metadata from database."""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute("DELETE FROM backups WHERE backup_id = ?", (backup_id,))
                conn.commit()

        except Exception as e:
            print(f"Error removing backup metadata: {e}")

    def list_backups(self, backup_type: str = None) -> List[Dict]:
        """
        List available backups.

        Args:
            backup_type: Filter by backup type (None for all)

        Returns:
            List of backup information
        """
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                if backup_type:
                    cursor = conn.execute(
                        """
                        SELECT backup_id, backup_type, created_at, file_path,
                               file_size, checksum, targets, status
                        FROM backups
                        WHERE backup_type = ?
                        ORDER BY created_at DESC
                    """,
                        (backup_type,),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT backup_id, backup_type, created_at, file_path,
                               file_size, checksum, targets, status
                        FROM backups
                        ORDER BY created_at DESC
                    """
                    )

                backups = []
                for row in cursor.fetchall():
                    backup_info = {
                        "backup_id": row[0],
                        "backup_type": row[1],
                        "created_at": row[2],
                        "file_path": row[3],
                        "file_size": row[4],
                        "file_size_mb": (
                            round(row[4] / (1024 * 1024), 2) if row[4] else 0
                        ),
                        "checksum": row[5],
                        "targets": json.loads(row[6]) if row[6] else [],
                        "status": row[7],
                        "exists": os.path.exists(row[3]) if row[3] else False,
                    }
                    backups.append(backup_info)

                return backups

        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

    def restore_backup(
        self, backup_id: str, targets: List[str] = None, restore_path: str = None
    ) -> bool:
        """
        Restore from backup.

        Args:
            backup_id: Backup ID to restore
            targets: List of targets to restore (None for all)
            restore_path: Custom restore path (None for original locations)

        Returns:
            True if restore successful, False otherwise
        """
        try:
            # Get backup information
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                print(f"Backup {backup_id} not found")
                return False

            backup_file = backup_info["file_path"]
            if not os.path.exists(backup_file):
                print(f"Backup file {backup_file} does not exist")
                return False

            # Verify checksum
            if not self._verify_backup(backup_file, backup_info["checksum"]):
                print(f"Backup file {backup_file} failed checksum verification")
                return False

            # Create restore directory
            restore_id = f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            temp_restore_dir = os.path.join(
                self.config["backup_dir"], "restore", restore_id
            )
            os.makedirs(temp_restore_dir, exist_ok=True)

            # Extract backup
            mode = "r:gz" if backup_file.endswith(".gz") else "r"

            with tarfile.open(backup_file, mode) as tar:
                if targets:
                    # Extract only specified targets
                    for target in targets:
                        try:
                            tar.extract(target, temp_restore_dir)
                        except KeyError:
                            print(f"Target {target} not found in backup")
                else:
                    # Extract all
                    tar.extractall(temp_restore_dir)

            # Restore to final locations
            success = self._restore_files(temp_restore_dir, targets, restore_path)

            if success:
                # Record restore operation
                self._record_restore(restore_id, backup_id, targets or [])

            # Clean up temporary directory
            shutil.rmtree(temp_restore_dir, ignore_errors=True)

            return success

        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

    def _get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """Get backup information from database."""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT backup_id, backup_type, created_at, file_path,
                           file_size, checksum, targets, status, metadata
                    FROM backups
                    WHERE backup_id = ?
                """,
                    (backup_id,),
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "backup_id": row[0],
                        "backup_type": row[1],
                        "created_at": row[2],
                        "file_path": row[3],
                        "file_size": row[4],
                        "checksum": row[5],
                        "targets": json.loads(row[6]) if row[6] else [],
                        "status": row[7],
                        "metadata": json.loads(row[8]) if row[8] else {},
                    }

        except Exception as e:
            print(f"Error getting backup info: {e}")

        return None

    def _verify_backup(self, backup_file: str, expected_checksum: str) -> bool:
        """Verify backup file integrity."""
        try:
            actual_checksum = self._calculate_checksum(backup_file)
            return actual_checksum == expected_checksum
        except Exception as e:
            print(f"Error verifying backup: {e}")
            return False

    def _restore_files(
        self, temp_dir: str, targets: List[str] = None, restore_path: str = None
    ) -> bool:
        """Restore files to their final locations."""
        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)

                if targets and item not in targets:
                    continue

                # Determine destination
                if restore_path:
                    dest_path = os.path.join(restore_path, item)
                else:
                    target_config = self.config["backup_targets"].get(item)
                    if target_config:
                        dest_path = target_config["path"]
                    else:
                        dest_path = os.path.join("/tmp/wade_restore", item)

                # Create destination directory
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # Copy files
                if os.path.isdir(item_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(item_path, dest_path)
                else:
                    shutil.copy2(item_path, dest_path)

                print(f"Restored {item} to {dest_path}")

            return True

        except Exception as e:
            print(f"Error restoring files: {e}")
            return False

    def _record_restore(self, restore_id: str, backup_id: str, targets: List[str]):
        """Record restore operation in database."""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO restore_points
                    (restore_id, backup_id, restored_targets, status)
                    VALUES (?, ?, ?, ?)
                """,
                    (restore_id, backup_id, json.dumps(targets), "completed"),
                )
                conn.commit()

        except Exception as e:
            print(f"Error recording restore: {e}")

    def start_scheduled_backups(self):
        """Start the scheduled backup service."""
        if self.running:
            return

        if not self.config["schedule"]["enabled"]:
            print("Scheduled backups are disabled")
            return

        self.running = True
        self.backup_thread = threading.Thread(
            target=self._backup_scheduler, daemon=True
        )
        self.backup_thread.start()
        print("Scheduled backup service started")

    def stop_scheduled_backups(self):
        """Stop the scheduled backup service."""
        self.running = False
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        print("Scheduled backup service stopped")

    def _backup_scheduler(self):
        """Background scheduler for automatic backups."""
        last_daily = None
        last_weekly = None
        last_monthly = None

        while self.running:
            try:
                now = datetime.now()

                # Check for daily backup
                daily_time = self.config["schedule"]["daily_time"]
                daily_hour, daily_minute = map(int, daily_time.split(":"))

                if (
                    now.hour == daily_hour
                    and now.minute == daily_minute
                    and (last_daily is None or last_daily.date() != now.date())
                ):

                    print("Starting scheduled daily backup")
                    backup_id = self.create_backup("daily")
                    if backup_id:
                        print(f"Daily backup completed: {backup_id}")
                        last_daily = now

                # Check for weekly backup
                weekly_day = self.config["schedule"]["weekly_day"].lower()
                weekdays = [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ]

                if (
                    now.strftime("%A").lower() == weekly_day
                    and now.hour == daily_hour
                    and now.minute == daily_minute
                    and (last_weekly is None or (now - last_weekly).days >= 7)
                ):

                    print("Starting scheduled weekly backup")
                    backup_id = self.create_backup("weekly")
                    if backup_id:
                        print(f"Weekly backup completed: {backup_id}")
                        last_weekly = now

                # Check for monthly backup
                monthly_day = self.config["schedule"]["monthly_day"]

                if (
                    now.day == monthly_day
                    and now.hour == daily_hour
                    and now.minute == daily_minute
                    and (last_monthly is None or last_monthly.month != now.month)
                ):

                    print("Starting scheduled monthly backup")
                    backup_id = self.create_backup("monthly")
                    if backup_id:
                        print(f"Monthly backup completed: {backup_id}")
                        last_monthly = now

                # Sleep for a minute
                time.sleep(60)

            except Exception as e:
                print(f"Error in backup scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

    def get_backup_stats(self) -> Dict:
        """Get backup statistics."""
        try:
            with sqlite3.connect(self.backup_db_path) as conn:
                # Total backups
                cursor = conn.execute("SELECT COUNT(*) FROM backups")
                total_backups = cursor.fetchone()[0]

                # Backups by type
                cursor = conn.execute(
                    """
                    SELECT backup_type, COUNT(*)
                    FROM backups
                    GROUP BY backup_type
                """
                )
                by_type = dict(cursor.fetchall())

                # Total size
                cursor = conn.execute("SELECT SUM(file_size) FROM backups")
                total_size = cursor.fetchone()[0] or 0

                # Recent backups
                cursor = conn.execute(
                    """
                    SELECT backup_id, backup_type, created_at
                    FROM backups
                    ORDER BY created_at DESC
                    LIMIT 5
                """
                )
                recent_backups = [
                    {"backup_id": row[0], "type": row[1], "created_at": row[2]}
                    for row in cursor.fetchall()
                ]

                return {
                    "total_backups": total_backups,
                    "by_type": by_type,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "recent_backups": recent_backups,
                    "backup_dir": self.config["backup_dir"],
                    "scheduled_enabled": self.config["schedule"]["enabled"],
                }

        except Exception as e:
            return {"error": str(e)}

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup.

        Args:
            backup_id: Backup ID to delete

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            backup_info = self._get_backup_info(backup_id)
            if not backup_info:
                return False

            # Remove backup file
            backup_file = backup_info["file_path"]
            if os.path.exists(backup_file):
                os.remove(backup_file)

            # Remove from database
            self._remove_backup_metadata(backup_id)

            print(f"Deleted backup: {backup_id}")
            return True

        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
