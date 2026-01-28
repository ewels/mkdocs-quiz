"""Tests for the QTI export functionality."""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from mkdocs_quiz.qti import (
    Blank,
    QTIExporter,
    QTIVersion,
    extract_quizzes_from_directory,
    extract_quizzes_from_file,
)
from mkdocs_quiz.qti.models import Answer, Quiz, QuizCollection


def parse_xml(xml_string: str) -> ET.Element:
    """Parse XML string and return root element, with helpful error messages.

    Args:
        xml_string: The XML content to parse.

    Returns:
        The root Element.

    Raises:
        AssertionError: If XML parsing fails, with context about the error.
    """
    try:
        return ET.fromstring(xml_string)
    except ET.ParseError as e:
        # Show first few lines of XML for context
        lines = xml_string.split("\n")
        preview = "\n".join(lines[:20])
        if len(lines) > 20:
            preview += f"\n... ({len(lines) - 20} more lines)"
        raise AssertionError(f"Failed to parse XML: {e}\n\nXML content:\n{preview}") from e


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

        # Quiz without answers or blanks
        no_answers = Quiz(question="Test?", answers=[])
        errors = no_answers.validate()
        assert "Quiz must have either answers or blanks" in errors

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
        root = parse_xml(manifest_xml)
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
        root = parse_xml(assessment_xml)
        assert "questestinterop" in root.tag

    def test_single_choice_item(self, sample_collection: QuizCollection) -> None:
        """Test single choice item XML."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V1_2)
        items = exporter.generate_items()

        # Find a single choice item
        for _filename, content in items.items():
            if "multiple_choice_question" in content:
                # Verify structure
                root = parse_xml(content)
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
                root = parse_xml(content)
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

        root = parse_xml(assessment_xml)
        assert "assessmentTest" in root.tag

    def test_qti21_item_structure(self, sample_collection: QuizCollection) -> None:
        """Test QTI 2.1 item structure."""
        exporter = QTIExporter.create(sample_collection, QTIVersion.V2_1)
        items = exporter.generate_items()

        assert len(items) == 1
        for _filename, content in items.items():
            root = parse_xml(content)
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


class TestFillInBlankModels:
    """Tests for fill-in-the-blank quiz models."""

    def test_blank_creation(self) -> None:
        """Test creating a Blank object."""
        blank = Blank(correct_answer="Paris")
        assert blank.correct_answer == "Paris"
        assert blank.identifier.startswith("blank_")

    def test_blank_strips_whitespace(self) -> None:
        """Test that Blank strips whitespace from answer."""
        blank = Blank(correct_answer="  London  ")
        assert blank.correct_answer == "London"

    def test_fill_in_blank_quiz_creation(self) -> None:
        """Test creating a fill-in-the-blank quiz."""
        blanks = [
            Blank(correct_answer="Paris"),
            Blank(correct_answer="France"),
        ]
        quiz = Quiz(
            question="The capital of {{BLANK_0}} is {{BLANK_1}}.",
            blanks=blanks,
        )
        assert quiz.is_fill_in_blank is True
        assert quiz.is_multiple_choice is False
        assert len(quiz.blanks) == 2

    def test_fill_in_blank_quiz_validation(self) -> None:
        """Test fill-in-blank quiz validation."""
        # Valid fill-in-blank quiz
        valid = Quiz(
            question="2 + 2 = {{BLANK_0}}",
            blanks=[Blank(correct_answer="4")],
        )
        assert valid.validate() == []

        # Quiz without question
        no_question = Quiz(question="", blanks=[Blank(correct_answer="4")])
        errors = no_question.validate()
        assert "Quiz must have a question" in errors

    def test_quiz_collection_fill_in_blank_count(self) -> None:
        """Test that QuizCollection correctly counts fill-in-blank quizzes."""
        collection = QuizCollection(title="Test")

        # Add multiple choice quiz
        collection.add_quiz(
            Quiz(
                question="What?",
                answers=[Answer(text="A", is_correct=True)],
            )
        )

        # Add fill-in-blank quiz
        collection.add_quiz(
            Quiz(
                question="Answer: {{BLANK_0}}",
                blanks=[Blank(correct_answer="test")],
            )
        )

        assert collection.total_questions == 2
        assert collection.single_choice_count == 1
        assert collection.fill_in_blank_count == 1


class TestFillInBlankExtractor:
    """Tests for fill-in-the-blank quiz extraction."""

    def test_extract_single_blank(self, tmp_path: Path) -> None:
        """Test extracting a quiz with a single blank."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
<quiz>
2 + 2 = [[4]]

---
Basic math!
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 1

        quiz = quizzes[0]
        assert quiz.is_fill_in_blank is True
        assert len(quiz.blanks) == 1
        assert quiz.blanks[0].correct_answer == "4"
        assert "{{BLANK_0}}" in quiz.question
        assert quiz.content is not None
        assert "math" in quiz.content

    def test_extract_multiple_blanks(self, tmp_path: Path) -> None:
        """Test extracting a quiz with multiple blanks."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
<quiz>
The [[cat]] sat on the [[mat]].
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 1

        quiz = quizzes[0]
        assert quiz.is_fill_in_blank is True
        assert len(quiz.blanks) == 2
        assert quiz.blanks[0].correct_answer == "cat"
        assert quiz.blanks[1].correct_answer == "mat"
        assert "{{BLANK_0}}" in quiz.question
        assert "{{BLANK_1}}" in quiz.question

    def test_extract_mixed_quiz_types(self, tmp_path: Path) -> None:
        """Test extracting both multiple-choice and fill-in-blank quizzes."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
<quiz>
What is 2+2?
- [x] 4
- [ ] 3
</quiz>

<quiz>
The answer is [[4]].
</quiz>
"""
        )

        quizzes = extract_quizzes_from_file(md_file)
        assert len(quizzes) == 2

        # First is multiple choice
        assert quizzes[0].is_fill_in_blank is False
        assert len(quizzes[0].answers) == 2

        # Second is fill-in-blank
        assert quizzes[1].is_fill_in_blank is True
        assert len(quizzes[1].blanks) == 1


class TestFillInBlankQTI12:
    """Tests for QTI 1.2 fill-in-the-blank export."""

    @pytest.fixture
    def fill_in_blank_collection(self) -> QuizCollection:
        """Create a collection with fill-in-blank quizzes."""
        collection = QuizCollection(title="Fill-in-Blank Test")

        # Single blank
        collection.add_quiz(
            Quiz(
                question="2 + 2 = {{BLANK_0}}",
                blanks=[Blank(correct_answer="4")],
                content="Basic arithmetic.",
            )
        )

        # Multiple blanks
        collection.add_quiz(
            Quiz(
                question="The {{BLANK_0}} sat on the {{BLANK_1}}.",
                blanks=[
                    Blank(correct_answer="cat"),
                    Blank(correct_answer="mat"),
                ],
            )
        )

        return collection

    def test_fill_in_blank_item_structure(self, fill_in_blank_collection: QuizCollection) -> None:
        """Test that fill-in-blank items have correct QTI 1.2 structure."""
        exporter = QTIExporter.create(fill_in_blank_collection, QTIVersion.V1_2)
        items = exporter.generate_items()

        assert len(items) == 2

        for _filename, content in items.items():
            # Verify it's valid XML
            root = parse_xml(content)
            assert "questestinterop" in root.tag

            # Check for fill-in-blank question type
            assert "fill_in_multiple_blanks_question" in content
            # Check for response_str (text entry)
            assert "response_str" in content
            assert "render_fib" in content

    def test_fill_in_blank_scoring(self, fill_in_blank_collection: QuizCollection) -> None:
        """Test that fill-in-blank items have correct scoring."""
        exporter = QTIExporter.create(fill_in_blank_collection, QTIVersion.V1_2)
        items = exporter.generate_items()

        for _filename, content in items.items():
            # Should have resprocessing for scoring
            assert "resprocessing" in content
            assert "varequal" in content


class TestFillInBlankQTI21:
    """Tests for QTI 2.1 fill-in-the-blank export."""

    @pytest.fixture
    def fill_in_blank_collection(self) -> QuizCollection:
        """Create a collection with fill-in-blank quizzes."""
        collection = QuizCollection(title="Fill-in-Blank Test 2.1")

        collection.add_quiz(
            Quiz(
                question="The capital of France is {{BLANK_0}}.",
                blanks=[Blank(correct_answer="Paris")],
            )
        )

        return collection

    def test_fill_in_blank_item_structure(self, fill_in_blank_collection: QuizCollection) -> None:
        """Test that fill-in-blank items have correct QTI 2.1 structure."""
        exporter = QTIExporter.create(fill_in_blank_collection, QTIVersion.V2_1)
        items = exporter.generate_items()

        assert len(items) == 1

        for _filename, content in items.items():
            # Verify it's valid XML
            root = parse_xml(content)
            assert "assessmentItem" in root.tag

            # Check for text entry interaction
            assert "textEntryInteraction" in content
            # Check for response declaration
            assert "responseDeclaration" in content
            assert 'baseType="string"' in content

    def test_fill_in_blank_response_processing(
        self, fill_in_blank_collection: QuizCollection
    ) -> None:
        """Test that fill-in-blank items have correct response processing."""
        exporter = QTIExporter.create(fill_in_blank_collection, QTIVersion.V2_1)
        items = exporter.generate_items()

        for _filename, content in items.items():
            # Should have string matching for text comparison
            assert "stringMatch" in content
            assert 'caseSensitive="false"' in content


class TestCDATAEscaping:
    """Tests for CDATA escaping in QTI export."""

    def test_cdata_end_sequence_escaped(self) -> None:
        """Test that ]]> in content is properly escaped."""
        from mkdocs_quiz.qti.utils import to_html_content

        # Content with CDATA end sequence
        text = "<p>Some code: array[i]]]> more text</p>"
        result = to_html_content(text)

        # Should be valid XML - the ]]> should be escaped
        assert "]]]]><![CDATA[>" in result

        # Verify the full CDATA is parseable as XML
        xml_test = f"<root>{result}</root>"
        root = parse_xml(xml_test)
        assert root is not None

    def test_html_without_cdata_sequence(self) -> None:
        """Test that normal HTML content is wrapped in CDATA."""
        from mkdocs_quiz.qti.utils import to_html_content

        text = "<p>Normal <b>HTML</b> content</p>"
        result = to_html_content(text)

        assert result.startswith("<![CDATA[")
        assert result.endswith("]]>")
        assert text in result

    def test_plain_text_escaped(self) -> None:
        """Test that plain text is XML-escaped, not CDATA-wrapped."""
        from mkdocs_quiz.qti.utils import to_html_content

        # Text without angle brackets should be XML-escaped
        text = "Simple text with special & characters"
        result = to_html_content(text)

        # Should be escaped, not CDATA
        assert "<![CDATA[" not in result
        assert "&amp;" in result

    def test_text_with_angle_brackets_uses_cdata(self) -> None:
        """Test that text with angle brackets (looks like HTML) uses CDATA."""
        from mkdocs_quiz.qti.utils import to_html_content

        # Text with angle brackets is treated as HTML and wrapped in CDATA
        text = "Code example: if (a < b && b > c)"
        result = to_html_content(text)

        # Contains < so uses CDATA
        assert "<![CDATA[" in result
