I immediately want to make some improvements to the plugin:

- [ ] No need for `content:` to be required when empty
- [ ] Parse questions and answers as markdown
- [ ] Option to show correct answer when wrong (rather than clicking each until it shows)
- [ ] Option to submit on selection for single-answer questions (no need for a "submit" button)
- [ ] Option to opt _in_ to having quiz JS included on a page, not just opt out
- [ ] Ability to track progress and score across the whole page
- [ ] Progress + score tracker in right hand sidebar
- [ ] Option to disable a question after initial submission (eg. show correct answer but don't allow original answer to be changed)
- [ ] Related: Ability to start again / clear all answers on the paeg
- [ ] Save progress in browser's local storage so that answers persist between page reloads
- [ ] Plugin option to customise syntax for question title (so doesn't have to be a `<h3>`
- [ ] Option to automatically number quiz questions down the page
- [ ] Include question header `id` with hover links to link directly to a specific question

And maybe nicer syntax for writing questions:

* Current syntax
    * ```markdown
      <?quiz?>
      question: Are you ready?
      answer-correct: Yes!
      answer: No!
      answer: Maybe!
      content:
      <h2>Some additional content here</h2>
      <?/quiz?>
      ```
* Proposed syntax
    * ```markdown
      <?quiz?>
      Are you ready?
      - [x] Yes!
      - [ ] No!
      - [ ] Maybe!
      Some additional content here
      <?/quiz?>
      ```
