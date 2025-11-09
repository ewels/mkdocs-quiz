# Quiz Results Screen

The quiz results screen provides a dynamic end-screen that tracks your progress and displays your final score when all questions are answered.

## How It Works

Add the special comment `<!-- mkdocs-quiz results -->` anywhere in your markdown to insert a results tracking panel. As you answer questions, it will show:

- Number of questions answered
- Number of correct answers
- Completion percentage

When all questions are answered, the display transforms into a celebratory completion screen with:

- A large, color-coded score display
- Encouraging messages based on your performance
- Confetti animation (if enabled)
- Automatic smooth scroll to bring the results into view
- A reset button to try again

## Try It Out!

Answer the two questions below to see the results screen in action.

<quiz>
What is the capital of France?
- [x] Paris
- [ ] London
- [ ] Berlin
- [ ] Madrid

Correct! Paris is the capital and largest city of France.
</quiz>

<quiz>
Which of these are programming languages?
- [x] Python
- [ ] HTML
- [x] JavaScript
- [ ] CSS

Great! Python and JavaScript are programming languages, while HTML and CSS are markup and styling languages respectively.
</quiz>

<!-- mkdocs-quiz results -->

## Configuration

### Confetti

The confetti animation is enabled by default but can be disabled in your `mkdocs.yml`:

```yaml
plugins:
  - mkdocs-quiz:
      confetti: false
```

Confetti only appears when:
- The confetti option is enabled
- All quizzes are completed
- Your score is 60% or higher

### Score Thresholds

The results screen uses color-coded feedback based on your score:

- **90%+**: Excellent (green) - "Outstanding! You're a quiz master!"
- **75-89%**: Good (light green) - "Great job! You really know your stuff!"
- **60-74%**: Average (yellow) - "Good effort! Keep learning!"
- **40-59%**: Poor (orange) - "Not bad, but there's room for improvement!"
- **Below 40%**: Fail (red) - "Better luck next time! Keep trying!"

## Usage

Simply add the comment where you want the results screen to appear:

```markdown
<quiz>
Your first quiz question here
- [x] Correct answer
- [ ] Wrong answer
</quiz>

<quiz>
Your second quiz question here
- [x] Correct answer
- [ ] Wrong answer
</quiz>

<!-- mkdocs-quiz results -->
```

The results screen will automatically track all quizzes on the page and update in real-time as answers are submitted.
