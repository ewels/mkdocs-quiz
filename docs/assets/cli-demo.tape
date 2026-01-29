# VHS tape file for generating CLI demo GIF
# Install vhs: https://github.com/charmbracelet/vhs
# Run: vhs docs/assets/cli-demo.tape

Output docs/assets/cli-demo.gif

Set Shell bash
Set FontSize 22
Set Width 1080
Set Height 720
Set Padding 20
Set Framerate 30
Set Theme "Catppuccin Mocha"
Set TypingSpeed 10ms

# Start the quiz
Type "quiz run docs/assets/demo-quiz.md"
Set TypingSpeed 50ms # Back to default
Sleep 500ms
Enter
Sleep 2.5s

# Question 1: Multiple choice (single) - select Paris
Down
Sleep 1.5s
Enter
Sleep 3s
Enter

# Question 2: Fill in the blank - type "programming"
Sleep 3s
Type "input"
Sleep 2s
Enter
Sleep 3s
Enter

# Question 3: Multiple choice (multi) - select Python and JavaScript
Sleep 3s
Space
Sleep 200ms
Down
Down
Sleep 200ms
Space
Sleep 1s
Enter
Sleep 3s
Enter

# Show final results
Sleep 3s
