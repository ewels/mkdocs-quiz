"""Base QTI exporter and common utilities.

This module provides the base class for QTI exporters and the version
enumeration for selecting export format.
"""

from __future__ import annotations

import io
import zipfile
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from .models import QuizCollection


class QTIVersion(Enum):
    """Supported QTI versions for export.

    Attributes:
        V1_2: QTI 1.2 - Widest compatibility (Canvas Classic Quizzes, Blackboard, older LMS)
        V2_1: QTI 2.1 - Modern standard (Canvas New Quizzes, Moodle 4+, newer LMS)
    """

    V1_2 = "1.2"
    V2_1 = "2.1"

    @classmethod
    def from_string(cls, version: str) -> QTIVersion:
        """Create QTIVersion from string.

        Args:
            version: Version string like "1.2" or "2.1"

        Returns:
            The corresponding QTIVersion enum value.

        Raises:
            ValueError: If version string is not recognized.
        """
        version = version.strip()
        for v in cls:
            if v.value == version:
                return v
        valid = ", ".join(v.value for v in cls)
        raise ValueError(f"Unknown QTI version: {version}. Valid options: {valid}")

    def __str__(self) -> str:
        return self.value


class QTIExporter(ABC):
    """Abstract base class for QTI exporters.

    Subclasses implement format-specific XML generation for different
    QTI versions.
    """

    def __init__(self, collection: QuizCollection) -> None:
        """Initialize the exporter with a quiz collection.

        Args:
            collection: The QuizCollection to export.
        """
        self.collection = collection

    @property
    @abstractmethod
    def version(self) -> QTIVersion:
        """Get the QTI version this exporter produces."""
        pass

    @abstractmethod
    def generate_manifest(self) -> str:
        """Generate the IMS manifest XML.

        Returns:
            The imsmanifest.xml content as a string.
        """
        pass

    @abstractmethod
    def generate_assessment(self) -> str:
        """Generate the assessment/test XML.

        Returns:
            The assessment XML content as a string.
        """
        pass

    @abstractmethod
    def generate_items(self) -> dict[str, str]:
        """Generate individual item XMLs.

        Returns:
            Dictionary mapping filenames to XML content.
        """
        pass

    def export_to_zip(self, output_path: str | Path) -> Path:
        """Export the quiz collection to a QTI ZIP package.

        Args:
            output_path: Path for the output ZIP file.

        Returns:
            The path to the created ZIP file.
        """
        output_path = Path(output_path)

        # Ensure .zip extension
        if output_path.suffix.lower() != ".zip":
            output_path = output_path.with_suffix(".zip")

        # Create the ZIP file
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add manifest
            zf.writestr("imsmanifest.xml", self.generate_manifest())

            # Add assessment
            zf.writestr("assessment.xml", self.generate_assessment())

            # Add individual items
            items = self.generate_items()
            for filename, content in items.items():
                zf.writestr(filename, content)

        return output_path

    def export_to_bytes(self) -> bytes:
        """Export the quiz collection to a QTI ZIP package in memory.

        Returns:
            The ZIP file content as bytes.
        """
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("imsmanifest.xml", self.generate_manifest())
            zf.writestr("assessment.xml", self.generate_assessment())

            items = self.generate_items()
            for filename, content in items.items():
                zf.writestr(filename, content)

        return buffer.getvalue()

    @classmethod
    def create(cls, collection: QuizCollection, version: QTIVersion) -> QTIExporter:
        """Factory method to create the appropriate exporter for a version.

        Args:
            collection: The QuizCollection to export.
            version: The QTI version to export to.

        Returns:
            An instance of the appropriate QTIExporter subclass.
        """
        # Import here to avoid circular imports
        from .qti12 import QTI12Exporter
        from .qti21 import QTI21Exporter

        exporters = {
            QTIVersion.V1_2: QTI12Exporter,
            QTIVersion.V2_1: QTI21Exporter,
        }

        exporter_class = exporters.get(version)
        if exporter_class is None:
            raise ValueError(f"No exporter available for QTI version {version}")

        return exporter_class(collection)
