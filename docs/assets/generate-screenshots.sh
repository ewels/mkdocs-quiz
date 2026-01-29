#!/usr/bin/env bash
# Generate documentation screenshots
#
# This script manages its own mkdocs server to ensure proper dark mode support.
#
# Prerequisites:
#   - npx playwright available
#
# Usage:
#   ./docs/assets/generate-screenshots.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCS_DIR="$PROJECT_DIR/docs"
IMAGES_DIR="$DOCS_DIR/images"
PORT="${PORT:-8765}"
BASE_URL="http://127.0.0.1:$PORT/mkdocs-quiz"

cd "$PROJECT_DIR"

echo "Generating documentation screenshots..."

# Kill any existing mkdocs server on our port
pkill -f "mkdocs serve.*$PORT" 2>/dev/null || true
sleep 1

# Backup mkdocs.yml
MKDOCS_YML="$PROJECT_DIR/mkdocs.yml"
cp "$MKDOCS_YML" "$MKDOCS_YML.bak"

# Function to restore mkdocs.yml and kill server on exit
cleanup() {
    echo "Cleaning up..."
    pkill -f "mkdocs serve.*$PORT" 2>/dev/null || true
    if [ -f "$MKDOCS_YML.bak" ]; then
        mv "$MKDOCS_YML.bak" "$MKDOCS_YML"
    fi
}
trap cleanup EXIT

# Enable media query-based dark mode by modifying mkdocs.yml
echo "Enabling automatic dark mode for screenshots..."
cat > /tmp/patch_mkdocs.py << 'EOF'
import sys
content = open(sys.argv[1]).read()
content = content.replace(
    '- scheme: default',
    '- media: "(prefers-color-scheme: light)"\n      scheme: default'
)
content = content.replace(
    '- scheme: slate',
    '- media: "(prefers-color-scheme: dark)"\n      scheme: slate'
)
open(sys.argv[1], 'w').write(content)
EOF
python3 /tmp/patch_mkdocs.py "$MKDOCS_YML"

# Start mkdocs server
echo "Starting mkdocs server on port $PORT..."
mkdocs serve --dev-addr "127.0.0.1:$PORT" &>/dev/null &
sleep 4

# Verify server is running
if ! curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" | grep -q "200"; then
    echo "Error: MkDocs server failed to start at $BASE_URL"
    exit 1
fi

echo "Server running at $BASE_URL"

# Create screenshot script with cropping support
cat > /tmp/take-screenshots.mjs << EOF
import { chromium } from 'playwright-core';

const BASE_URL = '$BASE_URL';
const IMAGES_DIR = '$IMAGES_DIR';

async function takeScreenshots() {
  const browser = await chromium.launch();

  // Desktop screenshots - crop to sidebar area (right side of page)
  console.log('Taking desktop screenshots...');
  const desktop = await browser.newPage({ viewport: { width: 1400, height: 900 } });

  // Light mode
  await desktop.goto(BASE_URL + '/multiple-choice/');
  await desktop.waitForTimeout(1000);
  await desktop.evaluate(() => {
    document.body.setAttribute('data-md-color-scheme', 'default');
  });
  await desktop.waitForTimeout(500);
  await desktop.screenshot({
    path: IMAGES_DIR + '/progress-sidebar.png',
    clip: { x: 1010, y: 0, width: 370, height: 335 }
  });
  console.log('  - progress-sidebar.png');

  // Dark mode
  await desktop.evaluate(() => {
    document.body.setAttribute('data-md-color-scheme', 'slate');
  });
  await desktop.waitForTimeout(500);
  await desktop.screenshot({
    path: IMAGES_DIR + '/progress-sidebar-dark.png',
    clip: { x: 1010, y: 0, width: 370, height: 335 }
  });
  console.log('  - progress-sidebar-dark.png');
  await desktop.close();

  // Mobile screenshots - crop to top progress bar
  console.log('Taking mobile screenshots...');
  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 } });

  // Light mode
  await mobile.goto(BASE_URL + '/multiple-choice/');
  await mobile.waitForTimeout(1000);
  await mobile.evaluate(() => {
    document.body.setAttribute('data-md-color-scheme', 'default');
  });
  await mobile.waitForTimeout(500);
  await mobile.screenshot({
    path: IMAGES_DIR + '/progress-mobile.png',
    clip: { x: 0, y: 0, width: 390, height: 200 }
  });
  console.log('  - progress-mobile.png');

  // Dark mode
  await mobile.evaluate(() => {
    document.body.setAttribute('data-md-color-scheme', 'slate');
  });
  await mobile.waitForTimeout(500);
  await mobile.screenshot({
    path: IMAGES_DIR + '/progress-mobile-dark.png',
    clip: { x: 0, y: 0, width: 390, height: 200 }
  });
  console.log('  - progress-mobile-dark.png');
  await mobile.close();

  await browser.close();
}

takeScreenshots().catch(err => {
  console.error(err);
  process.exit(1);
});
EOF

echo "Taking screenshots with cropping..."
NODE_PATH="$(npm root -g)" node /tmp/take-screenshots.mjs

echo ""
echo "Screenshots generated successfully!"
echo "  - $IMAGES_DIR/progress-sidebar.png"
echo "  - $IMAGES_DIR/progress-sidebar-dark.png"
echo "  - $IMAGES_DIR/progress-mobile.png"
echo "  - $IMAGES_DIR/progress-mobile-dark.png"
