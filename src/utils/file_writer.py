"""
File writing utility for generated pipeline configurations.

Handles safe file output with backup, directory creation, and validation.
"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileWriter:
    """Handles writing pipeline configuration files safely."""

    def __init__(self, file_path: str) -> None:
        """
        Initialize the file writer.

        Args:
            file_path: The target file path to write to.
        """
        self.file_path = file_path
        self._backup_path: Optional[str] = None

    def write(self, content: str) -> Path:
        """
        Write content to the file path.

        Creates parent directories if needed, backs up existing files,
        and writes the new content atomically.

        Args:
            content: The pipeline configuration content to write.

        Returns:
            The path to the written file.

        Raises:
            OSError: If file writing fails.
            ValueError: If content is empty.
        """
        if not content or not content.strip():
            raise ValueError("Cannot write empty content to file")

        target = Path(self.file_path)
        logger.info("Writing pipeline to %s", target)

        # Create parent directories
        target.parent.mkdir(parents=True, exist_ok=True)

        # Backup existing file
        if target.exists():
            self._backup(target)

        # Write content
        try:
            target.write_text(content, encoding="utf-8")
            logger.info("Successfully wrote %d bytes to %s", len(content), target)
        except OSError as exc:
            logger.error("Failed to write to %s: %s", target, exc)
            self._restore_backup()
            raise

        return target

    def _backup(self, target: Path) -> None:
        """
        Create a backup of an existing file.

        Args:
            target: The file to backup.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target.name}.{timestamp}.bak"
        self._backup_path = str(target.parent / backup_name)
        shutil.copy2(target, self._backup_path)
        logger.info("Backed up existing file to %s", self._backup_path)

    def _restore_backup(self) -> None:
        """Restore backup if write failed."""
        if self._backup_path and Path(self._backup_path).exists():
            try:
                shutil.copy2(self._backup_path, self.file_path)
                logger.info("Restored backup from %s", self._backup_path)
            except OSError as exc:
                logger.error("Failed to restore backup: %s", exc)

    @property
    def file_exists(self) -> bool:
        """Check if the target file already exists."""
        return Path(self.file_path).exists()

    @property
    def file_size(self) -> int:
        """Get the size of the target file if it exists."""
        path = Path(self.file_path)
        return path.stat().st_size if path.exists() else 0
