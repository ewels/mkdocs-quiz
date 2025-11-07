#!/bin/bash

# Migration script for mkdocs-quiz v2.0.0
# Converts old quiz syntax to new markdown-style syntax
#
# Usage: ./migrate_quiz_syntax.sh [directory]
#   directory - Path to search for .md files (default: docs/)
#
# Example: ./migrate_quiz_syntax.sh docs/

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get directory from argument or use default
SEARCH_DIR="${1:-docs}"

if [ ! -d "$SEARCH_DIR" ]; then
    echo -e "${RED}Error: Directory '$SEARCH_DIR' does not exist${NC}"
    exit 1
fi

echo -e "${GREEN}MkDocs Quiz Syntax Migration Script${NC}"
echo -e "Searching for quiz blocks in: ${YELLOW}$SEARCH_DIR${NC}"
echo ""

# Counter for stats
TOTAL_FILES=0
TOTAL_QUIZZES=0

# Find all markdown files containing quiz blocks
MD_FILES=$(find "$SEARCH_DIR" -name "*.md" -type f -exec grep -l "<?quiz?>" {} \;)

if [ -z "$MD_FILES" ]; then
    echo -e "${YELLOW}No quiz blocks found in markdown files.${NC}"
    exit 0
fi

# Process each file
for file in $MD_FILES; do
    echo -e "Processing: ${YELLOW}$file${NC}"

    # Create backup
    cp "$file" "$file.backup"

    # Create temp file for processing
    temp_file=$(mktemp)

    # Use Python for more robust parsing
    python3 << 'PYTHON_SCRIPT' "$file" "$temp_file"
import re
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r') as f:
    content = f.read()

# Pattern to match quiz blocks
quiz_pattern = r'<\?quiz\?>(.*?)<\?/quiz\?>'

def convert_quiz(match):
    quiz_content = match.group(1)
    lines = quiz_content.strip().split('\n')

    new_lines = []
    question = None
    answers = []
    content_lines = []
    in_content = False
    options = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Parse question
        if line.startswith('question:'):
            question = line.split('question:', 1)[1].strip()
        # Parse options
        elif line.startswith('show-correct:'):
            options.append(line)
        elif line.startswith('auto-submit:'):
            options.append(line)
        elif line.startswith('disable-after-submit:'):
            options.append(line)
        # Parse content separator
        elif line == 'content:':
            in_content = True
        # Parse answers
        elif line.startswith('answer-correct:'):
            answer_text = line.split('answer-correct:', 1)[1].strip()
            answers.append(('correct', answer_text))
        elif line.startswith('answer:'):
            answer_text = line.split('answer:', 1)[1].strip()
            answers.append(('incorrect', answer_text))
        # Content section
        elif in_content:
            content_lines.append(line)

    # Build new quiz format
    result = ['<?quiz?>']

    # Add question
    if question:
        result.append(question)

    # Add options
    for opt in options:
        result.append(opt)

    # Add answers in new format
    for answer_type, answer_text in answers:
        if answer_type == 'correct':
            result.append(f'- [x] {answer_text}')
        else:
            result.append(f'- [ ] {answer_text}')

    # Add content if present
    if content_lines:
        result.append('')  # Empty line before content
        result.extend(content_lines)

    result.append('<?/quiz?>')

    return '\n'.join(result)

# Replace all quiz blocks
new_content = re.sub(quiz_pattern, convert_quiz, content, flags=re.DOTALL)

with open(output_file, 'w') as f:
    f.write(new_content)

PYTHON_SCRIPT

    # Replace original file with converted version
    mv "$temp_file" "$file"

    # Count quizzes in this file
    QUIZ_COUNT=$(grep -o "<?quiz?>" "$file" | wc -l)
    TOTAL_QUIZZES=$((TOTAL_QUIZZES + QUIZ_COUNT))
    TOTAL_FILES=$((TOTAL_FILES + 1))

    echo -e "  ${GREEN}✓${NC} Converted $QUIZ_COUNT quiz(es)"
done

echo ""
echo -e "${GREEN}Migration complete!${NC}"
echo -e "  Files processed: ${YELLOW}$TOTAL_FILES${NC}"
echo -e "  Quizzes converted: ${YELLOW}$TOTAL_QUIZZES${NC}"
echo ""
echo -e "${YELLOW}Note: Backup files created with .backup extension${NC}"
echo -e "Review the changes and remove backups when satisfied:"
echo -e "  ${YELLOW}find $SEARCH_DIR -name '*.md.backup' -delete${NC}"
