// Global quiz tracker
const quizTracker = {
  quizzes: {},
  totalQuizzes: 0,
  answeredQuizzes: 0,
  correctQuizzes: 0,

  init: function () {
    this.totalQuizzes = document.querySelectorAll(".quiz").length;
    this.loadFromStorage();
    this.updateDisplay();
  },

  markQuiz: function (quizId, isCorrect, selectedValues = []) {
    const wasAnswered = !!this.quizzes[quizId];
    const wasCorrect = this.wasPreviouslyCorrect(quizId);

    if (!wasAnswered) {
      this.answeredQuizzes++;
    }

    this.quizzes[quizId] = {
      answered: true,
      correct: isCorrect,
      selectedValues: selectedValues,
    };

    if (isCorrect && !wasCorrect) {
      this.correctQuizzes++;
    } else if (!isCorrect && wasCorrect) {
      this.correctQuizzes--;
    }

    this.saveToStorage();
    this.updateDisplay();
  },

  wasPreviouslyCorrect: function (quizId) {
    return this.quizzes[quizId] && this.quizzes[quizId].correct;
  },

  resetQuiz: function (quizId) {
    if (this.quizzes[quizId]) {
      if (this.quizzes[quizId].correct) {
        this.correctQuizzes--;
      }
      this.answeredQuizzes--;
      delete this.quizzes[quizId];
      this.saveToStorage();
      this.updateDisplay();
    }
  },

  resetAllQuiz: function () {
    this.quizzes = {};
    this.answeredQuizzes = 0;
    this.correctQuizzes = 0;
    this.saveToStorage();
    this.updateDisplay();

    // Reset all quiz forms on the page
    document.querySelectorAll(".quiz").forEach((quiz) => {
      const form = quiz.querySelector("form");
      const fieldset = form.querySelector("fieldset");
      const submitButton = form.querySelector('button[type="submit"]');
      const resetButton = form.querySelector(".quiz-reset-button");
      const feedbackDiv = form.querySelector(".quiz-feedback");
      const section = quiz.querySelector("section");

      // Clear all selections
      const allInputs = fieldset.querySelectorAll('input[name="answer"]');
      allInputs.forEach((input) => {
        input.checked = false;
        input.disabled = false;
      });

      // Reset colors
      resetFieldset(fieldset);

      // Hide content section
      if (section) {
        section.classList.add("hidden");
      }

      // Hide feedback message
      feedbackDiv.classList.add("hidden");
      feedbackDiv.classList.remove("correct", "incorrect");
      feedbackDiv.textContent = "";

      // Show submit button, hide reset button
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.classList.remove("hidden");
      }
      if (resetButton) {
        resetButton.classList.add("hidden");
      }
    });
  },

  getProgress: function () {
    return {
      total: this.totalQuizzes,
      answered: this.answeredQuizzes,
      correct: this.correctQuizzes,
      percentage: this.totalQuizzes > 0 ? Math.round((this.answeredQuizzes / this.totalQuizzes) * 100) : 0,
      score: this.totalQuizzes > 0 ? Math.round((this.correctQuizzes / this.totalQuizzes) * 100) : 0,
    };
  },

  saveToStorage: function () {
    try {
      const pageKey = "quiz_progress_" + window.location.pathname;
      localStorage.setItem(pageKey, JSON.stringify(this.quizzes));
    } catch (e) {
      // Silently fail if localStorage is not available
    }
  },

  loadFromStorage: function () {
    try {
      const pageKey = "quiz_progress_" + window.location.pathname;
      const stored = localStorage.getItem(pageKey);
      if (stored) {
        this.quizzes = JSON.parse(stored);
        // Recalculate counts
        this.answeredQuizzes = 0;
        this.correctQuizzes = 0;
        for (let key in this.quizzes) {
          if (this.quizzes[key].answered) {
            this.answeredQuizzes++;
          }
          if (this.quizzes[key].correct) {
            this.correctQuizzes++;
          }
        }
      }
    } catch (e) {
      // Silently fail if localStorage is not available
    }
  },

  updateDisplay: function () {
    // Dispatch custom event for sidebar/other UI components
    window.dispatchEvent(
      new CustomEvent("quizProgressUpdate", {
        detail: this.getProgress(),
      }),
    );
    // Update sidebar if it exists
    this.updateSidebar();
  },

  updateSidebar: function () {
    const sidebar = document.getElementById("quiz-progress-sidebar");
    if (sidebar) {
      const progress = this.getProgress();

      // Update answered count
      const answeredEl = sidebar.querySelector(".quiz-progress-answered");
      if (answeredEl) {
        answeredEl.textContent = progress.answered;
      }

      // Update answered percentage
      const answeredPercentageEl = sidebar.querySelector(".quiz-progress-answered-percentage");
      if (answeredPercentageEl) {
        answeredPercentageEl.textContent = progress.percentage + "%";
      }

      // Update all .quiz-progress-total elements
      const totalElements = sidebar.querySelectorAll(".quiz-progress-total");
      totalElements.forEach((el) => {
        el.textContent = progress.total;
      });

      // Update correct count
      const scoreEl = sidebar.querySelector(".quiz-progress-score");
      if (scoreEl) {
        scoreEl.textContent = progress.correct;
      }

      // Update correct percentage
      const scorePercentageEl = sidebar.querySelector(".quiz-progress-score-percentage");
      if (scorePercentageEl) {
        scorePercentageEl.textContent = progress.score + "%";
      }

      // Update progress bars (incorrect and correct)
      const correctBar = sidebar.querySelector(".quiz-progress-bar-correct");
      const incorrectBar = sidebar.querySelector(".quiz-progress-bar-incorrect");

      if (correctBar && incorrectBar) {
        const incorrectCount = progress.answered - progress.correct;
        const correctPercentage = progress.total > 0 ? (progress.correct / progress.total) * 100 : 0;
        const incorrectPercentage = progress.total > 0 ? (incorrectCount / progress.total) * 100 : 0;

        incorrectBar.style.width = incorrectPercentage + "%";
        correctBar.style.width = correctPercentage + "%";
      }
    }
  },

  createSidebar: function () {
    // Only create sidebar if there are multiple quizzes
    if (this.totalQuizzes <= 1) {
      return;
    }

    const progress = this.getProgress();

    // Create nav element matching Material's TOC structure
    const nav = document.createElement("nav");
    nav.id = "quiz-progress-sidebar";
    nav.className = "md-nav md-nav--secondary";
    nav.setAttribute("aria-label", "Quiz Progress");

    nav.innerHTML = `
      <label class="md-nav__title" for="__quiz-progress">
        <span class="md-nav__icon md-icon"></span>
        Quiz Progress
      </label>
      <ul class="md-nav__list" data-md-component="quiz-progress">
        <li class="md-nav__item">
          <div class="md-nav__link">
            <span class="md-ellipsis">
              Answered: <span class="quiz-progress-answered">${progress.answered}</span> / <span class="quiz-progress-total">${progress.total}</span> (<span class="quiz-progress-answered-percentage">${progress.percentage}%</span>)
            </span>
          </div>
        </li>
        <li class="md-nav__item">
          <div class="md-nav__link">
            <div class="quiz-progress-bar">
              <div class="quiz-progress-bar-incorrect" style="width: ${progress.answered > progress.correct ? ((progress.answered - progress.correct) / progress.total) * 100 : 0}%"></div>
              <div class="quiz-progress-bar-correct" style="width: ${progress.score}%"></div>
            </div>
          </div>
        </li>
        <li class="md-nav__item">
          <div class="md-nav__link quiz-correct-reset">
            <span class="md-ellipsis">
              Correct: <span class="quiz-progress-score">${progress.correct}</span> / <span class="quiz-progress-total">${progress.total}</span> (<span class="quiz-progress-score-percentage">${progress.score}%</span>)
            </span>
            <a href="#" class="quiz-reset-all-link" style="color: var(--md-primary-fg-color); text-decoration: none;">
              Reset
            </a>
          </div>
        </li>
      </ul>
    `;

    // Replace the placeholder nav element (created by overridden main.html)
    // Fall back to article/body if placeholder doesn't exist
    const placeholder = document.getElementById("quiz-progress-sidebar-placeholder");
    if (placeholder && placeholder.parentNode) {
      // Replace the placeholder with the actual quiz progress sidebar
      placeholder.parentNode.replaceChild(nav, placeholder);
    } else {
      // Fallback: append to article/body if no placeholder found
      const container = document.querySelector("article") || document.querySelector("main") || document.body;
      container.appendChild(nav);
    }

    // Add event listener for reset link
    const resetLink = nav.querySelector(".quiz-reset-all-link");
    if (resetLink) {
      resetLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (confirm("Are you sure you want to reset the quiz? This will clear your progress.")) {
          quizTracker.resetAllQuiz();
        }
      });
    }
  },
};

// Initialize tracker
quizTracker.init();

// Create sidebar after page loads
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    quizTracker.createSidebar();
  });
} else {
  quizTracker.createSidebar();
}

document.querySelectorAll(".quiz").forEach((quiz) => {
  let form = quiz.querySelector("form");
  let fieldset = form.querySelector("fieldset");
  let submitButton = form.querySelector('button[type="submit"]');
  let feedbackDiv = form.querySelector(".quiz-feedback");

  // Get quiz ID from header
  const header = quiz.querySelector("h1, h2, h3, h4, h5, h6");
  const quizId = header ? header.id : null;

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

  // Restore quiz state from localStorage if available
  if (quizId && quizTracker.quizzes[quizId]) {
    const savedState = quizTracker.quizzes[quizId];
    const section = quiz.querySelector("section");
    const allAnswers = fieldset.querySelectorAll('input[name="answer"]');
    const correctAnswers = fieldset.querySelectorAll('input[name="answer"][correct]');

    if (savedState.answered) {
      // Restore selected answers based on saved values
      if (savedState.selectedValues && savedState.selectedValues.length > 0) {
        allAnswers.forEach((input) => {
          if (savedState.selectedValues.includes(input.value)) {
            input.checked = true;
          }
        });
      }

      if (savedState.correct) {
        // Show the content section
        section.classList.remove("hidden");

        // Mark all answers with colors
        allAnswers.forEach((input) => {
          if (input.hasAttribute("correct")) {
            input.parentElement.classList.add("correct");
          } else {
            input.parentElement.classList.add("wrong");
          }
        });

        // Show correct feedback
        feedbackDiv.classList.remove("hidden", "incorrect");
        feedbackDiv.classList.add("correct");
        feedbackDiv.textContent = "Correct answer!";

        // Disable inputs if disable-after-submit is enabled
        if (quiz.hasAttribute("data-disable-after-submit")) {
          allAnswers.forEach((input) => {
            input.disabled = true;
          });
          if (submitButton) {
            submitButton.disabled = true;
          }
          resetButton.classList.add("hidden");
        } else {
          // Show reset button, hide submit button
          resetButton.classList.remove("hidden");
          if (submitButton) {
            submitButton.classList.add("hidden");
          }
        }
      } else {
        // Restore incorrect answer state
        const selectedInputs = Array.from(allAnswers).filter((input) =>
          savedState.selectedValues.includes(input.value),
        );

        // Mark selected answers
        selectedInputs.forEach((input) => {
          if (input.hasAttribute("correct")) {
            input.parentElement.classList.add("correct");
          } else {
            input.parentElement.classList.add("wrong");
          }
        });

        // Show correct answers if show-correct is enabled
        if (quiz.hasAttribute("data-show-correct")) {
          correctAnswers.forEach((input) => {
            input.parentElement.classList.add("correct");
          });
        }

        // Show incorrect feedback
        feedbackDiv.classList.remove("hidden", "correct");
        feedbackDiv.classList.add("incorrect");
        const canRetry = !quiz.hasAttribute("data-disable-after-submit");
        feedbackDiv.textContent = canRetry ? "Incorrect answer. Please try again." : "Incorrect answer.";

        // Disable inputs if disable-after-submit is enabled
        if (quiz.hasAttribute("data-disable-after-submit")) {
          allAnswers.forEach((input) => {
            input.disabled = true;
          });
          if (submitButton) {
            submitButton.disabled = true;
          }
          resetButton.classList.add("hidden");
        } else {
          // Show reset button, hide submit button
          resetButton.classList.remove("hidden");
          if (submitButton) {
            submitButton.classList.add("hidden");
          }
        }
      }
    }
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
    // Hide feedback message
    feedbackDiv.classList.add("hidden");
    feedbackDiv.classList.remove("correct", "incorrect");
    feedbackDiv.textContent = "";
    // Show submit button, hide reset button
    if (submitButton) {
      submitButton.disabled = false;
      submitButton.classList.remove("hidden");
    }
    resetButton.classList.add("hidden");
    // Update tracker
    if (quizId) {
      quizTracker.resetQuiz(quizId);
    }
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
      // Show correct feedback
      feedbackDiv.classList.remove("hidden", "incorrect");
      feedbackDiv.classList.add("correct");
      feedbackDiv.textContent = "Correct answer!";
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
      // Show incorrect feedback
      feedbackDiv.classList.remove("hidden", "correct");
      feedbackDiv.classList.add("incorrect");
      // Only show "Please try again" if the quiz is not disabled after submission
      const canRetry = !quiz.hasAttribute("data-disable-after-submit");
      feedbackDiv.textContent = canRetry ? "Incorrect answer. Please try again." : "Incorrect answer.";
    }

    // Update tracker
    if (quizId) {
      // Get selected values to save
      const selectedValues = Array.from(selectedAnswers).map((input) => input.value);
      quizTracker.markQuiz(quizId, is_correct, selectedValues);
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
