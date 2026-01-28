# QTI Export

MkDocs Quiz can export your quizzes to QTI (Question and Test Interoperability) format for import into Learning Management Systems (LMS) like Canvas, Blackboard, and Moodle.

## Usage

Export quizzes using the `mkdocs-quiz export qti` command:

```bash
# Export all quizzes from the docs/ directory
mkdocs-quiz export qti docs/

# Export with custom output filename and title
mkdocs-quiz export qti docs/ -o my-quiz.zip -t "My Course Quiz"

# Export from a single file
mkdocs-quiz export qti docs/chapter1.md
```

### Command Options

| Option                | Description                                   |
| --------------------- | --------------------------------------------- |
| `path`                | Source markdown file or directory (required)  |
| `-o`, `--output`      | Output ZIP file path (default: `quizzes.zip`) |
| `-q`, `--qti-version` | QTI version: `1.2` or `2.1` (default: `1.2`)  |
| `-t`, `--title`       | Title for the quiz package                    |
| `--no-recursive`      | Don't search directories recursively          |

## QTI Versions

| Version | Flag               | Best For                                      |
| ------- | ------------------ | --------------------------------------------- |
| QTI 1.2 | `-q 1.2` (default) | Canvas Classic Quizzes, Blackboard, older LMS |
| QTI 2.1 | `-q 2.1`           | Canvas New Quizzes, Moodle 4+, modern LMS     |

!!! tip "Which version should I use?"

    If you're unsure, start with **QTI 1.2** (the default) as it has the widest compatibility. If your LMS doesn't accept it, try QTI 2.1.

## Question Type Mapping

| MkDocs Quiz Type                      | QTI Type          |
| ------------------------------------- | ----------------- |
| Single correct answer (radio buttons) | Multiple Choice   |
| Multiple correct answers (checkboxes) | Multiple Response |
| Fill-in-the-blank (`[[answer]]`)      | Text Entry        |

Quiz explanations (content after the answers) are exported as feedback, shown after the student answers.

## Importing into LMS Platforms

### Canvas

1. Go to your course settings
2. Click "Import Course Content"
3. Select "QTI .zip file"
4. Upload your exported ZIP file

### Blackboard

1. Go to Course Tools > Tests, Surveys, and Pools
2. Click "Import Test"
3. Upload your QTI 1.2 ZIP file

### Moodle

1. Go to your course's Question Bank
2. Click "Import"
3. For QTI support, you may need an additional plugin

!!! note

    Import steps may vary depending on your LMS version. Consult your LMS documentation for specific instructions.

## Limitations

- **Rich content**: HTML formatting is preserved, but complex elements may not render in all LMS platforms
- **Images**: Images are not bundled in the export; use absolute URLs
- **Scoring**: Default scoring is used (full points for correct answers)
- **Fill-in-the-blank**: Answers are matched case-insensitively, but LMS platforms may handle matching differently
