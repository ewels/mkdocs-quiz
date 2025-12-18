---
quiz:
  shuffle_answers: true
---

# Shuffle Answers

The `shuffle_answers` option randomizes the order of answer choices on every page load. This prevents users from memorizing answer positions rather than learning the content.

Enable it globally in `mkdocs.yml`:

```yaml
plugins:
  - mkdocs_quiz:
      shuffle_answers: true
```

Or per-page via frontmatter:

```yaml
---
quiz:
  shuffle_answers: true
---
```

Refresh this page a few times to see the answers appear in different orders.

<quiz>
What is the capital of France?

- [ ] London
- [ ] Berlin
- [x] Paris
- [ ] Madrid

</quiz>

<quiz>
Which of these are programming languages?

- [x] Python
- [ ] HTML
- [x] JavaScript
- [ ] CSS

Select all that apply.
</quiz>

<quiz>
What year did the first Moon landing occur?

- [ ] 1965
- [ ] 1967
- [x] 1969
- [ ] 1971

</quiz>
