// Wrap everything in an IIFE to avoid variable redeclaration issues
// when Material for MkDocs instant navigation reloads the page
(function () {
  // Constants
  const STORAGE_KEY_PREFIX = "quiz_progress_";

  // Translation helper function
  function t(key, params = {}) {
    let text = window.mkdocsQuizTranslations?.[key] || key;
    // Simple template replacement for {n} and {key} style placeholders
    return text.replace(/{(\w+)}/g, (_, k) => (params[k] !== undefined ? params[k] : `{${k}}`));
  }

  // Confetti instance (will be initialized if enabled)
  let jsConfetti = null;

  // Store event listeners for cleanup
  let eventListeners = [];

  // Initialize confetti if enabled
  if (window.mkdocsQuizConfig && window.mkdocsQuizConfig.confetti) {
    if (typeof JSConfetti !== "undefined") {
      jsConfetti = new JSConfetti();
    }
  }

  // Function to move quiz progress sidebar into TOC sidebar
  // This needs to run on every page load for Material instant navigation
  function repositionSidebar() {
    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
      const sidebar = document.getElementById("quiz-progress-sidebar");
      const tocSidebar = document.querySelector(".md-sidebar--secondary .md-sidebar__inner .md-nav--secondary");

      if (sidebar && tocSidebar) {
        // Check if sidebar is already in the correct position
        // by seeing if it's already a child of tocSidebar
        if (!tocSidebar.contains(sidebar)) {
          // Get position from config (default: "top")
          const position =
            window.mkdocsQuizConfig && window.mkdocsQuizConfig.progressSidebarPosition
              ? window.mkdocsQuizConfig.progressSidebarPosition
              : "top";

          // Move sidebar based on configured position
          if (position === "bottom") {
            // Append to the end (below TOC)
            tocSidebar.appendChild(sidebar);
          } else {
            // Default: insert at the top (above TOC)
            if (tocSidebar.firstChild) {
              tocSidebar.insertBefore(sidebar, tocSidebar.firstChild);
            } else {
              tocSidebar.appendChild(sidebar);
            }
          }
        }
      }
    });
  }

  // Cleanup function to remove event listeners and prevent memory leaks
  function cleanup() {
    eventListeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler);
    });
    eventListeners = [];
  }

  // Helper function to add tracked event listeners
  function addTrackedEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    eventListeners.push({ element, event, handler });
  }

  // Global quiz tracker
  const quizTracker = {
    quizzes: {},
    totalQuizzes: 0,
    answeredQuizzes: 0,
    correctQuizzes: 0,

    init: function () {
      this.totalQuizzes = document.querySelectorAll(".quiz").length;
      this.loadFromStorage();
      // Initialize wasCompleted based on restored state to prevent confetti on page load
      // Only fire confetti when completing quizzes in the current session, not from localStorage
      const progress = this.getProgress();
      this.wasCompleted = progress.answered === progress.total && progress.total > 0;
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
        const pageKey = STORAGE_KEY_PREFIX + window.location.pathname;
        const data = JSON.stringify(this.quizzes);

        // Check size limit (50KB max to prevent quota issues)
        if (data.length > 50000) {
          console.warn("Quiz progress data exceeds size limit, not saving to localStorage");
          this.showStorageWarning("Quiz progress is too large to save");
          return;
        }

        localStorage.setItem(pageKey, data);
      } catch (e) {
        // Handle quota exceeded or localStorage disabled
        console.error("Failed to save quiz progress:", e);
        this.showStorageWarning(
          "Unable to save quiz progress. Your browser may have storage disabled or quota exceeded.",
        );
      }
    },

    loadFromStorage: function () {
      try {
        const pageKey = STORAGE_KEY_PREFIX + window.location.pathname;
        const stored = localStorage.getItem(pageKey);

        if (stored) {
          // Validate size before parsing (50KB max)
          if (stored.length > 50000) {
            console.warn("Stored quiz data exceeds size limit, clearing corrupted data");
            localStorage.removeItem(pageKey);
            return;
          }

          const parsed = JSON.parse(stored);

          // Validate structure: should be an object
          if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
            console.warn("Invalid quiz data structure, clearing corrupted data");
            localStorage.removeItem(pageKey);
            return;
          }

          this.quizzes = parsed;

          // Recalculate counts and validate quiz data structure
          this.answeredQuizzes = 0;
          this.correctQuizzes = 0;
          for (let key in this.quizzes) {
            const quiz = this.quizzes[key];
            // Validate each quiz entry has expected structure
            if (typeof quiz !== "object" || typeof quiz.answered !== "boolean" || typeof quiz.correct !== "boolean") {
              console.warn("Invalid quiz entry structure, clearing corrupted data");
              this.quizzes = {};
              localStorage.removeItem(pageKey);
              return;
            }

            if (quiz.answered) {
              this.answeredQuizzes++;
            }
            if (quiz.correct) {
              this.correctQuizzes++;
            }
          }
        }
      } catch (e) {
        // Handle parsing errors or localStorage unavailable
        console.error("Failed to load quiz progress:", e);
        const pageKey = STORAGE_KEY_PREFIX + window.location.pathname;
        try {
          localStorage.removeItem(pageKey); // Clear corrupted data
        } catch (cleanupError) {
          // localStorage might be completely unavailable
        }
      }
    },

    updateDisplay: function () {
      const progress = this.getProgress();
      const wasComplete = this.wasCompleted;
      const isComplete = progress.answered === progress.total && progress.total > 0;

      // Dispatch custom event for sidebar/other UI components
      window.dispatchEvent(
        new CustomEvent("quizProgressUpdate", {
          detail: progress,
        }),
      );
      // Update sidebar if it exists
      this.updateSidebar();
      // Update results div if it exists
      this.updateResultsDiv(progress, isComplete, wasComplete);

      // Track completion state
      this.wasCompleted = isComplete;
    },

    updateResultsDiv: function (progress, isComplete, wasComplete) {
      const resultsDiv = document.getElementById("quiz-results");
      if (!resultsDiv) return;

      // Update progress section
      const answeredEl = resultsDiv.querySelector(".quiz-results-answered");
      const totalEl = resultsDiv.querySelector(".quiz-results-total");
      const percentageEl = resultsDiv.querySelector(".quiz-results-percentage");
      const correctEl = resultsDiv.querySelector(".quiz-results-correct");

      if (answeredEl) answeredEl.textContent = progress.answered;
      if (totalEl) totalEl.textContent = progress.total;
      if (percentageEl) percentageEl.textContent = progress.percentage + "%";
      if (correctEl) correctEl.textContent = progress.correct;

      // Handle completion state
      const progressSection = resultsDiv.querySelector(".quiz-results-progress");
      const completeSection = resultsDiv.querySelector(".quiz-results-complete");

      if (isComplete) {
        // Hide progress, show complete
        if (progressSection) progressSection.classList.add("hidden");
        if (completeSection) {
          completeSection.classList.remove("hidden");

          // Update score display
          const scoreValue = resultsDiv.querySelector(".quiz-results-score-value");
          const scoreMessage = resultsDiv.querySelector(".quiz-results-message");

          if (scoreValue) {
            scoreValue.textContent = progress.score + "%";

            // Remove all score classes
            scoreValue.classList.remove(
              "quiz-results-score-excellent",
              "quiz-results-score-good",
              "quiz-results-score-average",
              "quiz-results-score-poor",
              "quiz-results-score-fail",
            );

            // Add appropriate score class and message
            let message = "";
            if (progress.score >= 90) {
              scoreValue.classList.add("quiz-results-score-excellent");
              message = t("Outstanding! You aced it!");
            } else if (progress.score >= 75) {
              scoreValue.classList.add("quiz-results-score-good");
              message = t("Great job! You really know your stuff!");
            } else if (progress.score >= 60) {
              scoreValue.classList.add("quiz-results-score-average");
              message = t("Good effort! Keep learning!");
            } else if (progress.score >= 40) {
              scoreValue.classList.add("quiz-results-score-poor");
              message = t("Not bad, but there's room for improvement!");
            } else {
              scoreValue.classList.add("quiz-results-score-fail");
              message = t("Better luck next time! Keep trying!");
            }

            if (scoreMessage) scoreMessage.textContent = message;
          }

          // Trigger confetti and scroll on first completion
          if (!wasComplete) {
            // Scroll to results div
            resultsDiv.scrollIntoView({ behavior: "smooth", block: "center" });

            // Fire confetti if enabled and score is good
            if (jsConfetti && progress.score >= 10) {
              setTimeout(() => {
                jsConfetti.addConfetti();
              }, 500);
            }
          }
        }
      } else {
        // Show progress, hide complete
        if (progressSection) progressSection.classList.remove("hidden");
        if (completeSection) completeSection.classList.add("hidden");
      }
    },

    updateSidebar: function () {
      // Update both desktop and mobile sidebars
      const sidebars = [
        document.getElementById("quiz-progress-sidebar"),
        document.getElementById("quiz-progress-mobile"),
      ];

      sidebars.forEach((sidebar) => {
        if (sidebar) {
          const progress = this.getProgress();

          // Update answered count
          const answeredEl = sidebar.querySelector(".quiz-progress-answered");
          if (answeredEl) {
            answeredEl.textContent = progress.answered;
          }

          // Update answered percentage - desktop only
          const answeredPercentageEl = sidebar.querySelector(".quiz-progress-answered-percentage");
          if (answeredPercentageEl && sidebar.id == "quiz-progress-sidebar") {
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

          // Update correct denominator (answered count)
          const scoreTotalEl = sidebar.querySelector(".quiz-progress-score-total");
          if (scoreTotalEl) {
            scoreTotalEl.textContent = progress.answered;
          }

          // Update correct percentage (based on answered quizzes, not total) - desktop only
          const scorePercentageEl = sidebar.querySelector(".quiz-progress-score-percentage");
          if (scorePercentageEl && sidebar.id == "quiz-progress-sidebar") {
            const scorePercentage =
              progress.answered > 0 ? Math.round((progress.correct / progress.answered) * 100) : 0;
            scorePercentageEl.textContent = scorePercentage + "%";
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
      });
    },

    createSidebar: function () {
      // Check if progress tracking is enabled
      const showProgress = window.mkdocsQuizConfig && window.mkdocsQuizConfig.showProgress !== false;

      // Only show sidebar if progress tracking is enabled and there are quizzes
      if (!showProgress || this.totalQuizzes === 0) {
        return;
      }

      // Show both desktop and mobile sidebars
      const desktopSidebar = document.getElementById("quiz-progress-sidebar");
      const mobileSidebar = document.getElementById("quiz-progress-mobile");

      if (desktopSidebar) {
        desktopSidebar.style.display = "";
      }
      if (mobileSidebar) {
        mobileSidebar.style.display = "";
      }

      // Initialize reset button event listeners
      const resetLinks = document.querySelectorAll(".quiz-reset-all-link");
      resetLinks.forEach((resetLink) => {
        const handler = (e) => {
          e.preventDefault();
          if (confirm(t("Are you sure you want to reset the quiz? This will clear your progress."))) {
            quizTracker.resetAllQuiz();
          }
        };
        addTrackedEventListener(resetLink, "click", handler);
      });

      // Update the sidebar with initial values
      this.updateSidebar();
    },

    showStorageWarning: function (message) {
      // Show a warning banner in the progress tracker if it exists
      const progressSidebar = document.getElementById("quiz-progress-sidebar");
      if (progressSidebar) {
        // Check if warning already exists
        let warningEl = progressSidebar.querySelector(".quiz-storage-warning");
        if (!warningEl) {
          warningEl = document.createElement("div");
          warningEl.className = "quiz-storage-warning";
          warningEl.style.cssText =
            "background: #fff3cd; color: #856404; padding: 8px; margin: 8px 0; border-radius: 4px; font-size: 12px; border: 1px solid #ffeaa7;";
          progressSidebar.insertBefore(warningEl, progressSidebar.firstChild);
        }
        warningEl.textContent = message;
      }
    },
  };

  // Translate template elements with data-quiz-translate attributes
  function translateTemplateElements() {
    document.querySelectorAll("[data-quiz-translate]").forEach((element) => {
      const key = element.getAttribute("data-quiz-translate");
      if (key) {
        element.textContent = t(key);
      }
    });
  }

  // Initialize tracker
  quizTracker.init();

  // Translate template elements
  translateTemplateElements();

  // Reposition sidebar for Material theme TOC integration
  // Must run on every page load to support instant navigation
  repositionSidebar();

  // Create sidebar after page loads
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      translateTemplateElements();
      repositionSidebar();
      quizTracker.createSidebar();
      initializeResultsDiv();
      initializeIntroResetButtons();
    });
  } else {
    quizTracker.createSidebar();
    initializeResultsDiv();
    initializeIntroResetButtons();
  }

  // Initialize results div reset button
  function initializeResultsDiv() {
    const resultsDiv = document.getElementById("quiz-results");
    if (!resultsDiv) return;

    const resetButton = resultsDiv.querySelector(".quiz-results-reset");
    if (resetButton) {
      const handler = () => {
        if (confirm(t("Are you sure you want to reset the quiz? This will clear your progress."))) {
          quizTracker.resetAllQuiz();
        }
      };
      addTrackedEventListener(resetButton, "click", handler);
    }
  }

  // Initialize intro reset buttons
  function initializeIntroResetButtons() {
    const introResetButtons = document.querySelectorAll(".quiz-intro-reset");
    introResetButtons.forEach((button) => {
      const handler = () => {
        if (confirm(t("Are you sure you want to reset the quiz? This will clear your progress."))) {
          quizTracker.resetAllQuiz();
        }
      };
      addTrackedEventListener(button, "click", handler);
    });
  }

  document.querySelectorAll(".quiz").forEach((quiz) => {
    let form = quiz.querySelector("form");
    let fieldset = form.querySelector("fieldset");
    let submitButton = form.querySelector('button[type="submit"]');
    let feedbackDiv = form.querySelector(".quiz-feedback");

    // Get quiz ID from the quiz div itself
    const quizId = quiz.id;

    // Prevent anchor link from triggering page navigation/reload
    const headerLink = quiz.querySelector(".quiz-header-link");
    if (headerLink) {
      const handler = (e) => {
        // Let the browser handle the anchor navigation normally
        // This prevents Material for MkDocs from intercepting it as a page navigation
        e.stopPropagation();
      };
      addTrackedEventListener(headerLink, "click", handler);
    }

    // Create reset button (initially hidden)
    let resetButton = document.createElement("button");
    resetButton.type = "button";
    resetButton.className = "quiz-button quiz-reset-button hidden";
    resetButton.textContent = t("Try Again");
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

          // Only mark the correct answers in green (don't highlight wrong answers)
          allAnswers.forEach((input) => {
            if (input.hasAttribute("correct")) {
              input.parentElement.classList.add("correct");
            }
          });

          // Show correct feedback
          feedbackDiv.classList.remove("hidden", "incorrect");
          feedbackDiv.classList.add("correct");
          feedbackDiv.textContent = t("Correct answer!");

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

          // Show the content section for incorrect answers too
          section.classList.remove("hidden");

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
          feedbackDiv.textContent = canRetry ? t("Incorrect answer. Please try again.") : t("Incorrect answer.");

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
        const handler = () => {
          // Trigger form submission
          form.dispatchEvent(new Event("submit"));
        };
        addTrackedEventListener(radio, "change", handler);
      });
    }

    // Reset button handler
    const resetHandler = () => {
      // Clear all selections
      const allInputs = fieldset.querySelectorAll('input[name="answer"]');
      allInputs.forEach((input) => {
        input.checked = false;
        input.disabled = false;
      });
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
    };
    addTrackedEventListener(resetButton, "click", resetHandler);

    const submitHandler = (event) => {
      event.preventDefault();
      let selectedAnswers = form.querySelectorAll('input[name="answer"]:checked');
      let correctAnswers = fieldset.querySelectorAll('input[name="answer"][correct]');
      // Check if all correct answers are selected
      let is_correct = selectedAnswers.length === correctAnswers.length;
      Array.from(selectedAnswers).forEach((answer) => {
        if (!answer.hasAttribute("correct")) {
          is_correct = false;
        }
      });
      let section = quiz.querySelector("section");
      // Always show the content section after submission
      section.classList.remove("hidden");

      if (is_correct) {
        resetFieldset(fieldset);
        // Only mark the correct answers in green (don't highlight wrong answers)
        const allAnswers = fieldset.querySelectorAll('input[name="answer"]');
        allAnswers.forEach((answer) => {
          if (answer.hasAttribute("correct")) {
            answer.parentElement.classList.add("correct");
          }
        });
        // Show correct feedback
        feedbackDiv.classList.remove("hidden", "incorrect");
        feedbackDiv.classList.add("correct");
        feedbackDiv.textContent = t("Correct answer!");
      } else {
        resetFieldset(fieldset);
        // Mark wrong fields with colors
        Array.from(selectedAnswers).forEach((answer) => {
          if (!answer.hasAttribute("correct")) {
            answer.parentElement.classList.add("wrong");
          } else {
            answer.parentElement.classList.add("correct");
          }
        });
        // If show-correct is enabled, also show all correct answers
        if (quiz.hasAttribute("data-show-correct")) {
          correctAnswers.forEach((answer) => {
            answer.parentElement.classList.add("correct");
          });
        }
        // Show incorrect feedback
        feedbackDiv.classList.remove("hidden", "correct");
        feedbackDiv.classList.add("incorrect");
        // Only show "Please try again" if the quiz is not disabled after submission
        const canRetry = !quiz.hasAttribute("data-disable-after-submit");
        feedbackDiv.textContent = canRetry ? t("Incorrect answer. Please try again.") : t("Incorrect answer.");
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
        allInputs.forEach((input) => {
          input.disabled = true;
        });
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
    };
    addTrackedEventListener(form, "submit", submitHandler);
  });

  function resetFieldset(fieldset) {
    Array.from(fieldset.children).forEach((child) => {
      child.classList.remove("wrong", "correct");
    });
  }

  // Material for MkDocs instant navigation support
  // Cleanup and reinitialize when navigating between pages
  if (typeof document$ !== "undefined") {
    // Material theme with instant navigation is active
    document$.subscribe(() => {
      cleanup(); // Remove old event listeners to prevent memory leaks
      // The IIFE will re-run when the new page content loads
    });
  }
})(); // End of IIFE
