"""Tests for the QTI export functionality."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from mkdocs_quiz.qti import (
    QTIExporter,
    QTIVersion,
    extract_quizzes_from_directory,
    extract_quizzes_from_file,
)
from mkdocs_quiz.qti.models import Answer, Quiz, QuizCollection


class TestModels:
    """Tests for the QTI data models."""

    def test_answer_creation(self) -> None:
        """Test creating an Answer object."""
        answer = Answer(text="Test answer", is_correct=True)
        assert answer.text == "Test answer"
        assert answer.is_correct is True
        assert answer.identifier.startswith("answer_")

    def test_answer_strips_whitespace(self) -> None:
        """Test that Answer strips whitespace from text."""
        answer = Answer(text="  Padded answer  ", is_correct=False)
        assert answer.text == "Padded answer"

    def test_quiz_creation(self) -> None:
        """Test creating a Quiz object."""
        answers = [
            Answer(text="Correct", is_correct=True),
            Answer(text="Wrong", is_correct=False),
        ]
        quiz = Quiz(question="Test question?", answers=answers)
        assert quiz.question == "Test question?"
        assert len(quiz.answers) == 2
        assert quiz.identifier.startswith("quiz_")

    def test_quiz_is_multiple_choice(self) -> None:
        """Test the is_multiple_choice property."""
        single_choice = Quiz(
            question="Single?",
            answers=[
                Answer(text="A", is_correct=True),
                Answer(text="B", is_correct=False),
            ],
        )
        assert single_choice.is_multiple_choice is False

        multiple_choice = Quiz(
            question="Multiple?",
            answers=[
                Answer(text="A", is_correct=True),
                Answer(text="B", is_correct=True),
                Answer(text="C", is_correct=False),
            ],
        )
        assert multiple_choice.is_multiple_choice is True

    def test_quiz_correct_answers(self) -> None:
        """Test the correct_answers property."""
        quiz = Quiz(
            question="Test?",
            answers=[
                Answer(text="Correct 1", is_correct=True),
                Answer(text="Wrong", is_correct=False),
                Answer(text="Correct 2", is_correct=True),
            ],
        )
        correct = quiz.correct_answers
        assert len(correct) == 2
        assert all(a.is_correct for a in correct)

    def test_quiz_validation(self) -> None:
        """Test quiz validation."""
        # Valid quiz
        valid = Quiz(
            question="Test?",
            answers=[Answer(text="A", is_correct=True)],
        )
        assert valid.validate() == []

        # Quiz without question
        no_question = Quiz(question="", answers=[Answer(text="A", is_correct=True)])
        errors = no_question.validate()
        assert "Quiz must have a question" in errors

        # Quiz without answers
        no_answers = Quiz(question="Test?", answers=[])
        errors = no_answers.validate()
        assert "Quiz must have at least one answer" in errors

        # Quiz without correct answer
        no_correct = Quiz(
            question="Test?",
            answers=[Answer(text="A", is_correct=False)],
        )
        errors = no_correct.validate()
        assert "Quiz must have at least one correct answer" in errors

    def test_quiz_collection(self) -> None:
        """Test QuizCollection."""
        collection = QuizCollection(title="Test Collection")
        assert collection.total_questions == 0

        quiz1 = Quiz(
            question="Q1?",
            answers=[Answer(text="A", is_correct=True)],
        )
        quiz2 = Quiz(
            question="Q2?",
            answers=[
                Answer(text="A", is_correct=True),
                Answer(text="B", is_correct=True),
            ],
        )

        collection.add_quiz(quiz1)
        collection.add_quiz(quiz2)

        assert collection.total_questions == 2
        assert collection.single_choice_count == 1
        assert collection.multiple_choice_count == 1


class TestExtractor:
    """Tests for the quiz extractor."""

    def test_extract_single_quiz(self, tmp_path: Path) -> None:
        """Test extracting a single quiz from a file."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
# Test Quiz

<quiz>
What is 2+2?
- [x] 4
- [ ] 3
- [ ] 5

The answer is 4 because math.
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 1

        quiz = quizzes[0]
        assert "What is 2+2?" in quiz.question
        assert len(quiz.answers) == 3
        assert quiz.answers[0].is_correct is True
        assert quiz.answers[1].is_correct is False
        assert quiz.content is not None
        assert "math" in quiz.content

    def test_extract_multiple_quizzes(self, tmp_path: Path) -> None:
        """Test extracting multiple quizzes from a file."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
<quiz>
Question 1?
- [x] Yes
- [ ] No
</quiz>

Some text between.

<quiz>
Question 2?
- [ ] A
- [x] B
- [x] C
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 2
        assert "Question 1?" in quizzes[0].question
        assert "Question 2?" in quizzes[1].question
        assert quizzes[1].is_multiple_choice is True

    def test_extract_from_directory(self, tmp_path: Path) -> None:
        """Test extracting quizzes from a directory."""
        # Create subdirectory
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        # Create files
        (tmp_path / "file1.md").write_text(
            """
<quiz>
Q1?
- [x] A
</quiz>
"""
        )
        (subdir / "file2.md").write_text(
            """
<quiz>
Q2?
- [x] B
</quiz>
"""
        )

        collection = extract_quizzes_from_directory(tmp_path)
        assert collection.total_questions == 2

    def test_extract_ignores_code_blocks(self, tmp_path: Path) -> None:
        """Test that quizzes in code blocks are ignored."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
Here's an example:

```markdown
<quiz>
This is just an example
- [x] Not real
</quiz>
```

<quiz>
Real question?
- [x] Yes
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 1
        assert "Real question?" in quizzes[0].question


class TestQTIVersion:
    """Tests for QTI version handling."""

    def test_version_from_string(self) -> None:
        """Test creating QTIVersion from string."""
        assert QTIVersion.from_string("1.2") == QTIVersion.V1_2
        assert QTIVersion.from_string("2.1") == QTIVersion.V2_1

    def test_version_from_string_invalid(self) -> None:
        """Test that invalid version raises error."""
        with pytest.raises(ValueError, match="Unknown QTI version"):
            QTIVersion.from_string("3.0")

    def test_version_str(self) -> None:
        """Test version string representation."""
        assert str(QTIVersion.V1_2) == "1.2"
        assert str(QTIVersion.V2_1) == "2.1"


class TestQTI12Export:
    """Tests for QTI 1.2 export."""

    @pytest.fixture
    def sample_collection(self) -> QuizCollection:
        """Create a sample quiz collection for testing."""
        collection = QuizCollection(title="Test Quiz", description="Test description")

        # Single choice question
        collection.add_quiz(
            Quiz(
                question="What is 2+2?",
                answers=[
                    Answer(text="4", is_correct=True),
                    Answer(text="3", is_correct=False),
                    Answer(text="5", is_correct=False),
                ],
                content="The answer is 4.",
            )
        )

        # Multiple choice question
        collection.add_quiz(
            Quiz(
                question="Which are fruits?",
                answers=[
                    Answer(text="Apple", is_correct=True),
                    Answer(text="Banana", is_correct=True),
                    Answer(text="Carrot", is_correct=False),
                ],
            )
        )

        return collection

    def test_export_creates_valid_zip(self, sample_collection: QuizCollection) -> None:
        """Test that export creates a valid ZIP file."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = exporter.export_to_zip(output_path)
            assert result.exists()

            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                assert "imsmanifest.xml" in names
                assert "assessment.xml" in names
                assert any(n.startswith("items/") for n in names)
        finally:
            output_path.unlink(missing_ok=True)

    def test_export_to_bytes(self, sample_collection: QuizCollection) -> None:
        """Test exporting to bytes."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        data = exporter.export_to_bytes()

        assert len(data) > 0
        # Verify it's a valid ZIP
        import io

        with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
            assert "imsmanifest.xml" in zf.namelist()

    def test_manifest_structure(self, sample_collection: QuizCollection) -> None:
        """Test the manifest XML structure."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        manifest_xml = exporter.generate_manifest()

        # Parse and verify structure
        root = ET.fromstring(manifest_xml)
        assert root.tag == "{http://www.imsglobal.org/xsd/imscp_v1p1}manifest"

        # Check for resources
        resources = root.find(".//{http://www.imsglobal.org/xsd/imscp_v1p1}resources")
        assert resources is not None
        assert len(list(resources)) > 0

    def test_assessment_structure(self, sample_collection: QuizCollection) -> None:
        """Test the assessment XML structure."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        assessment_xml = exporter.generate_assessment()

        # Parse and verify
        root = ET.fromstring(assessment_xml)
        assert "questestinterop" in root.tag

    def test_single_choice_item(self, sample_collection: QuizCollection) -> None:
        """Test single choice item XML."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        items = exporter.generate_items()

        # Find a single choice item
        for _filename, content in items.items():
            if "multiple_choice_question" in content:
                # Verify structure
                root = ET.fromstring(content)
                assert "questestinterop" in root.tag
                # Check for Single cardinality
                assert "Single" in content or "rcardinality" in content
                break

    def test_multiple_choice_item(self, sample_collection: QuizCollection) -> None:
        """Test multiple choice item XML."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        items = exporter.generate_items()

        # Find a multiple choice item
        for _filename, content in items.items():
            if "multiple_answers_question" in content:
                root = ET.fromstring(content)
                assert "questestinterop" in root.tag
                assert "Multiple" in content
                break


class TestQTI21Export:
    """Tests for QTI 2.1 export."""

    @pytest.fixture
    def sample_collection(self) -> QuizCollection:
        """Create a sample quiz collection for testing."""
        collection = QuizCollection(title="Test Quiz 2.1")

        collection.add_quiz(
            Quiz(
                question="Test question?",
                answers=[
                    Answer(text="Correct", is_correct=True),
                    Answer(text="Wrong", is_correct=False),
                ],
            )
        )

        return collection

    def test_qti21_export_creates_zip(self, sample_collection: QuizCollection) -> None:
        """Test QTI 2.1 export creates a valid ZIP."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V2_1)

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            output_path = Path(f.name)

        try:
            result = exporter.export_to_zip(output_path)
            assert result.exists()

            with zipfile.ZipFile(result, "r") as zf:
                names = zf.namelist()
                assert "imsmanifest.xml" in names
                assert "assessment.xml" in names
        finally:
            output_path.unlink(missing_ok=True)

    def test_qti21_assessment_structure(self, sample_collection: QuizCollection) -> None:
        """Test QTI 2.1 assessment structure."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V2_1)
        assessment_xml = exporter.generate_assessment()

        root = ET.fromstring(assessment_xml)
        assert "assessmentTest" in root.tag

    def test_qti21_item_structure(self, sample_collection: QuizCollection) -> None:
        """Test QTI 2.1 item structure."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V2_1)
        items = exporter.generate_items()

        assert len(items) == 1
        for _filename, content in items.items():
            root = ET.fromstring(content)
            assert "assessmentItem" in root.tag


class TestExporterFactory:
    """Tests for the exporter factory."""

    def test_create_qti12(self) -> None:
        """Test creating QTI 1.2 exporter."""
        collection = QuizCollection(title="Test")
        exporter = QTIExporter.create(collection, QTIVersion.V1_2)
        assert exporter.version == QTIVersion.V1_2

    def test_create_qti21(self) -> None:
        """Test creating QTI 2.1 exporter."""
        collection = QuizCollection(title="Test")
        exporter = QTIExporter.create(collection, QTIVersion.V2_1)
        assert exporter.version == QTIVersion.V2_1
