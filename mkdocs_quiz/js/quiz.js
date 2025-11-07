document.querySelectorAll(".quiz").forEach((quiz) => {
  let form = quiz.querySelector("form");
  let fieldset = form.querySelector("fieldset");
  let submitButton = form.querySelector('button[type="submit"]');

  // Create reset button (initially hidden)
  let resetButton = document.createElement("button");
  resetButton.type = "button";
  resetButton.className = "quiz-button quiz-reset-button hidden";
  resetButton.textContent = "Try Again";
  if (submitButton) {
    submitButton.parentNode.insertBefore(resetButton, submitButton.nextSibling);
  } else {
    form.appendChild(resetButton);
  }

  // Auto-submit on radio button change if enabled
  if (quiz.hasAttribute("data-auto-submit")) {
    let radioButtons = fieldset.querySelectorAll('input[type="radio"]');
    radioButtons.forEach((radio) => {
      radio.addEventListener("change", () => {
        // Trigger form submission
        form.dispatchEvent(new Event("submit"));
      });
    });
  }

  // Reset button handler
  resetButton.addEventListener("click", () => {
    // Clear all selections
    const allInputs = fieldset.querySelectorAll('input[name="answer"]');
    for (let i = 0; i < allInputs.length; i++) {
      allInputs[i].checked = false;
      allInputs[i].disabled = false;
    }
    // Reset colors
    resetFieldset(fieldset);
    // Hide content section
    let section = quiz.querySelector("section");
    section.classList.add("hidden");
    // Show submit button, hide reset button
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.classList.remove("hidden");
    }
    resetButton.classList.add("hidden");
  });

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

    // Disable quiz after submission if option is enabled
    if (quiz.hasAttribute("data-disable-after-submit")) {
      const allInputs = fieldset.querySelectorAll('input[name="answer"]');
      for (let i = 0; i < allInputs.length; i++) {
        allInputs[i].disabled = true;
      }
      if (submitButton) {
        submitButton.disabled = true;
      }
      // Hide reset button if disable-after-submit is enabled
      resetButton.classList.add("hidden");
    } else {
      // Show reset button and hide submit button
      resetButton.classList.remove("hidden");
      if (submitButton) {
        submitButton.classList.add("hidden");
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
