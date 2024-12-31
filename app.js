document.addEventListener("DOMContentLoaded", () => {
    const gradeSelect = document.getElementById("grade");
    const chapterSelect = document.getElementById("chapter");
    const startTestButton = document.getElementById("start-test");
    const questionContainer = document.getElementById("question-container");
    const questionText = document.getElementById("question-text");
    const answerInput = document.getElementById("answer");
    const submitAnswerButton = document.getElementById("submit-answer");
    const nextQuestionButton = document.getElementById("next-question"); // New "Next Question" button
    const endTestButton = document.getElementById("end-test");
    const feedbackContainer = document.getElementById("feedback-container");
    const feedbackText = document.getElementById("feedback");

    let currentTopic = null; // Will hold the current chapter/topic

    // Fetch chapters when a grade is selected
    gradeSelect.addEventListener("change", () => {
        const grade = gradeSelect.value;
        if (grade) {
            fetch("/get_chapters", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ grade })
            })
                .then((response) => response.json())
                .then((chapters) => {
                    chapterSelect.innerHTML = "<option value=''>Select a Chapter</option>";
                    chapters.forEach((chapter) => {
                        const option = document.createElement("option");
                        option.value = chapter;
                        option.textContent = chapter;
                        chapterSelect.appendChild(option);
                    });
                })
                .catch((error) => console.error("Error fetching chapters:", error));
        }
    });

    // Start the test
    startTestButton.addEventListener("click", () => {
        const grade = gradeSelect.value;
        const chapter = chapterSelect.value;

        if (grade && chapter) {
            fetch("/start_test", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ grade, chapter })
            })
                .then((response) => response.json())
                .then((data) => {
                    currentTopic = chapter;  // Ensure currentTopic is set correctly
                    feedbackContainer.style.display = "none";
                    questionContainer.style.display = "block";
                    getNextQuestion();  // Get the first question
                })
                .catch((error) => console.error("Error starting test:", error));
        } else {
            alert("Please select a grade and chapter to start the test.");
        }
    });

    // Get the next question
    function getNextQuestion(lastAnswer = null) {
        // Ensure that currentTopic is included in the request
        fetch("/next_question", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                last_answer: lastAnswer,
                current_topic: currentTopic  // Send the current topic for the next question
            })
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.question) {
                    feedbackContainer.style.display = "none";
                    questionText.textContent = data.question;
                    answerInput.value = "";
                    // Show the "Submit Answer" button and hide "Next Question" until after the answer is submitted
                    submitAnswerButton.style.display = "block";
                    nextQuestionButton.style.display = "none";
                } else {
                    feedbackText.textContent = "No more questions available.";
                    feedbackContainer.style.display = "block";
                    questionContainer.style.display = "none";
                }
            })
            .catch((error) => console.error("Error fetching question:", error));
    }

    // Submit an answer
    submitAnswerButton.addEventListener("click", () => {
        const answer = answerInput.value.trim();
        if (answer) {
            fetch("/submit_answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    answer,
                    current_topic: currentTopic  // Send the current topic with the answer
                })
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.feedback) {
                        feedbackText.textContent = data.feedback;
                        feedbackContainer.style.display = "block";
                        // Hide the "Submit Answer" button and show the "Next Question" button
                        submitAnswerButton.style.display = "none";
                        nextQuestionButton.style.display = "block";
                    }
                })
                .catch((error) => console.error("Error submitting answer:", error));
        } else {
            alert("Please provide an answer before submitting.");
        }
    });

    // Proceed to the next question when the "Next Question" button is clicked
    nextQuestionButton.addEventListener("click", () => {
        getNextQuestion(); // Call getNextQuestion() to load the next question
    });

    // End the test
    endTestButton.addEventListener("click", () => {
        fetch("/end_test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        })
            .then((response) => response.json())
            .then((data) => {
                alert("Test ended. Performance data:\n" + JSON.stringify(data.performance, null, 2));
                feedbackContainer.style.display = "none";
                questionContainer.style.display = "none";
                gradeSelect.value = "";
                chapterSelect.innerHTML = "<option value=''>Select a Chapter</option>";
            })
            .catch((error) => console.error("Error ending test:", error));
    });
});
