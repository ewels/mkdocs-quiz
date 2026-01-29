# Progress Tracking

MkDocs Quiz includes a progress tracking system that helps users monitor their quiz completion status. Progress is automatically saved to the browser's local storage.

## Progress Sidebar

When a page has **two or more quizzes**, a progress tracker automatically appears in the right sidebar (on Material theme). It shows:

- **Answered count**: How many quizzes have been completed
- **Progress bar**: Visual representation of completion
- **Score breakdown**: Correct and incorrect answer counts
- **Reset link**: Clear all progress on the page

<figure markdown="span" style="border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px; padding: 1rem;">
![Progress sidebar](images/progress-sidebar.png#only-light)
![Progress sidebar](images/progress-sidebar-dark.png#only-dark)
</figure>

## Mobile Progress Bar

On mobile devices, a sticky progress bar appears at the top of the page instead of the sidebar:

<figure markdown="span" style="border: 1px solid var(--md-default-fg-color--lightest); border-radius: 4px; padding: 1rem;">
![Mobile progress bar](images/progress-mobile.png#only-light){ width="300" }
![Mobile progress bar](images/progress-mobile-dark.png#only-dark){ width="300" }
</figure>

## Local Storage Persistence

Quiz progress is automatically saved to the browser's local storage. This means:

- **Progress persists** across page reloads and browser sessions
- **Per-page storage**: Each page tracks its own quiz state independently
- **Answer restoration**: Previously submitted answers are restored when returning to a page

!!! tip "Privacy Note"
Quiz data is stored locally in the user's browser only. No data is sent to any server.

## Resetting Progress

Users can reset quiz progress in several ways:

### From the Progress Sidebar

Click the "Reset" link in the progress sidebar to clear all quiz progress on the current page.

### Using Intro Text

Add the intro text comment to provide users with a reset button:

```markdown
<!-- mkdocs-quiz intro -->
```

This displays an info panel explaining that progress is saved, along with a reset button. See [Intro Text](intro-text.md) for more details.

### Programmatically

For advanced use cases, you can reset progress via JavaScript:

```javascript
// Clear progress for current page
localStorage.removeItem("quizProgress_" + window.location.pathname);
location.reload();
```

## Configuration

### Hiding the Progress Tracker

To hide the progress sidebar and mobile bar on specific pages:

```yaml title="page.md frontmatter"
---
quiz:
  show_progress: false
---
```

Or disable site-wide:

```yaml title="mkdocs.yml"
plugins:
  - mkdocs_quiz:
      show_progress: false
```

### Sidebar Position

Control where the progress tracker appears in the sidebar:

```yaml title="mkdocs.yml"
plugins:
  - mkdocs_quiz:
      progress_sidebar_position: bottom # or "top" (default)
```

- `top` (default): Progress tracker appears above the Table of Contents
- `bottom`: Progress tracker appears below the Table of Contents

This is useful for pages with substantial content where quizzes appear at the end.

## Try It Out

Answer the quizzes below to see the progress tracker in action:

<quiz>
What color is the sky on a clear day?
- [x] Blue
- [ ] Green
- [ ] Red
</quiz>

<quiz>
How many continents are there?
- [ ] 5
- [ ] 6
- [x] 7
- [ ] 8
</quiz>

<quiz>
What is 10 + 5?
- [ ] 10
- [x] 15
- [ ] 20
</quiz>

Look at the sidebar (desktop) or top of the page (mobile) to see your progress!

## Events for Integration

The quiz system dispatches custom events that you can use for integration:

```javascript
document.addEventListener("quizProgressUpdate", function (e) {
  console.log("Quiz progress updated:", e.detail);
  // e.detail contains: { answered, total, correct, incorrect }
});
```

This allows you to build custom progress displays or integrate with analytics.

## Next Steps

- Add an [Intro Text](intro-text.md) panel with reset functionality
- Configure the [Results Screen](results-screen.md) for completion celebrations
- See all options in [Configuration](configuration.md)
