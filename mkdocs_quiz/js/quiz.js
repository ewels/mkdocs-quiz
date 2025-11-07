document.querySelectorAll(".quiz").forEach((quiz) => {
  let form = quiz.querySelector("form");
  let fieldset = form.querySelector("fieldset");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    let selectedAnswers = form.querySelectorAll('input[name="answer"]:checked');
    let correctAnswers = fieldset.querySelectorAll('input[name="answer"][correct]');
    // Check if all correct answers are selected
    let is_correct = selectedAnswers.length === correctAnswers.length;
    for (let i = 0; i < selectedAnswers.length; i++) {
      if (!selectedAnswers[i].hasAttribute("correct")) {
        is_correct = false;
        break;
      }
    }
    let section = quiz.querySelector("section");
    if (is_correct) {
      section.classList.remove("hidden");
      resetFieldset(fieldset);
      // Mark all fields with colors
      const allAnswers = fieldset.querySelectorAll('input[name="answer"]');
      for (let i = 0; i < allAnswers.length; i++) {
        if (allAnswers[i].hasAttribute("correct")) {
          allAnswers[i].parentElement.classList.add("correct");
        } else {
          allAnswers[i].parentElement.classList.add("wrong");
        }
      }
    } else {
      section.classList.add("hidden");
      resetFieldset(fieldset);
      // Mark wrong fields with colors
      for (let i = 0; i < selectedAnswers.length; i++) {
        if (!selectedAnswers[i].hasAttribute("correct")) {
          selectedAnswers[i].parentElement.classList.add("wrong");
        } else {
          selectedAnswers[i].parentElement.classList.add("correct");
        }
      }
      // If show-correct is enabled, also show all correct answers
      if (quiz.hasAttribute("data-show-correct")) {
        for (let i = 0; i < correctAnswers.length; i++) {
          correctAnswers[i].parentElement.classList.add("correct");
        }
      }
    }
  });
});

function resetFieldset(fieldset) {
  const fieldsetChildren = fieldset.children;
  for (let i = 0; i < fieldsetChildren.length; i++) {
    fieldsetChildren[i].classList.remove("wrong");
    fieldsetChildren[i].classList.remove("correct");
  }
}
