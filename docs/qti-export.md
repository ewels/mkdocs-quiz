# QTI Export

MkDocs Quiz can export your quizzes to QTI (Question and Test Interoperability) format for import into Learning Management Systems (LMS) like Canvas, Blackboard, and Moodle.

## Overview

QTI is an IMS Global standard for representing assessments and quiz questions in a portable format. Exporting your quizzes to QTI allows you to:

- Import quizzes into Canvas, Blackboard, Moodle, and other LMS platforms
- Reuse quiz content across different systems
- Create assessments from your documentation

## Usage

Export quizzes using the `mkdocs-quiz export qti` command:

```bash
# Export all quizzes from the docs/ directory
mkdocs-quiz export qti docs/

# Export with a custom output filename
mkdocs-quiz export qti docs/ -o my-quiz.zip

# Set a custom title for the quiz package
mkdocs-quiz export qti docs/ -t "My Course Quiz"

# Export from a single file
mkdocs-quiz export qti docs/chapter1.md
```

## QTI Versions

The plugin supports two QTI versions:

| Version | Flag               | Best For                                      |
| ------- | ------------------ | --------------------------------------------- |
| QTI 1.2 | `-q 1.2` (default) | Canvas Classic Quizzes, Blackboard, older LMS |
| QTI 2.1 | `-q 2.1`           | Canvas New Quizzes, Moodle 4+, modern LMS     |

```bash
# Export as QTI 1.2 (default)
mkdocs-quiz export qti docs/

# Export as QTI 2.1
mkdocs-quiz export qti docs/ -q 2.1
```

!!! tip "Which version should I use?"
If you're unsure which version to use, start with **QTI 1.2** (the default). It has the widest compatibility across LMS platforms. If your LMS doesn't accept it, try QTI 2.1.

## Command Options

| Option                | Description                                   |
| --------------------- | --------------------------------------------- |
| `path`                | Source markdown file or directory (required)  |
| `-o`, `--output`      | Output ZIP file path (default: `quizzes.zip`) |
| `-q`, `--qti-version` | QTI version: `1.2` or `2.1` (default: `1.2`)  |
| `-t`, `--title`       | Title for the quiz package                    |
| `--no-recursive`      | Don't search directories recursively          |

## Examples

### Export a Course's Quizzes

```bash
# Export all quizzes from a course directory
mkdocs-quiz export qti docs/python-course/ -t "Python Fundamentals" -o python-quiz.zip
```

### Export for Canvas

For Canvas Classic Quizzes, use QTI 1.2:

```bash
mkdocs-quiz export qti docs/ -q 1.2 -o canvas-import.zip
```

For Canvas New Quizzes, use QTI 2.1:

```bash
mkdocs-quiz export qti docs/ -q 2.1 -o canvas-new-quiz.zip
```

### Export a Single Page

```bash
mkdocs-quiz export qti docs/chapter-5-review.md -t "Chapter 5 Review Quiz"
```

## Importing into LMS Platforms

### Canvas

1. Go to your course settings
2. Click "Import Course Content"
3. Select "QTI .zip file"
4. Upload your exported ZIP file
5. Click "Import"

### Blackboard

1. Go to Course Tools > Tests, Surveys, and Pools
2. Click "Import Test"
3. Upload your QTI 1.2 ZIP file
4. Follow the import wizard

### Moodle

1. Go to your course's Question Bank
2. Click "Import"
3. Select "Moodle XML format" or "GIFT format" (for QTI, you may need an additional plugin)
4. Upload your exported file

!!! note
Import steps may vary depending on your LMS version. Consult your LMS documentation for specific instructions.

## Question Type Mapping

| MkDocs Quiz Type                      | QTI Type          |
| ------------------------------------- | ----------------- |
| Single correct answer (radio buttons) | Multiple Choice   |
| Multiple correct answers (checkboxes) | Multiple Response |
| Fill-in-the-blank (`[[answer]]`)      | Text Entry        |

### Single Choice Example

This quiz syntax:

```markdown
<quiz>
What is 2 + 2?
- [ ] 3
- [x] 4
- [ ] 5
</quiz>
```

Exports as a "Multiple Choice" question where the student selects one answer.

### Multiple Choice Example

This quiz syntax:

```markdown
<quiz>
Which are prime numbers?
- [x] 2
- [x] 3
- [ ] 4
- [x] 5
</quiz>
```

Exports as a "Multiple Response" question where the student must select all correct answers.

### Fill-in-the-Blank Example

This quiz syntax:

```markdown
<quiz>
The capital of France is [[Paris]].
</quiz>
```

Exports as a "Text Entry" question where the student types their answer. Multiple blanks in a single question are supported:

```markdown
<quiz>
The [[cat]] sat on the [[mat]].
</quiz>
```

## Export Package Structure

The exported ZIP file follows the IMS Content Package format:

```
quizzes.zip
├── imsmanifest.xml      # Package manifest
├── assessment.xml       # Quiz metadata
└── items/               # Individual questions
    ├── quiz_abc123.xml
    └── quiz_def456.xml
```

## Feedback and Explanations

If your quiz includes content after the answers (the explanation section), it will be exported as feedback in the QTI package:

```markdown
<quiz>
What is the capital of France?
- [x] Paris
- [ ] London
- [ ] Berlin

Paris has been the capital of France since the late 10th century.
</quiz>
```

The explanation text will appear as feedback after the student answers the question (if supported by the LMS).

## Limitations

- **Rich content**: HTML formatting in questions and answers is preserved, but complex elements may not render in all LMS platforms
- **Images**: Images referenced in quizzes are not bundled in the export; use absolute URLs for images
- **Scoring**: Default scoring is used (full points for correct answers)
- **Fill-in-the-blank matching**: Text entry answers are matched case-insensitively, but some LMS platforms may handle matching differently
