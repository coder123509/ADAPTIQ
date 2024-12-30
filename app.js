document.addEventListener('DOMContentLoaded', () => {
    const gradeSelect = document.getElementById('grade');
    const chapterSelect = document.getElementById('chapter');
    const questionSection = document.getElementById('questionSection');
    const feedbackSection = document.getElementById('feedbackSection');
    const selectionForm = document.getElementById('selectionForm');
    const questionType = document.getElementById('questionType');
    const questionText = document.getElementById('questionText');
    const feedbackText = document.getElementById('feedbackText');
    const answerInput = document.getElementById('answer');
    const submitAnswerBtn = document.getElementById('submitAnswer');
    const nextQuestionBtn = document.getElementById('nextQuestion');

    // Fetch grades and populate the grade dropdown
    fetch('/')
        .then((response) => response.json())
        .then((grades) => {
            gradeSelect.innerHTML = '<option value="" disabled selected>Select Grade</option>';
            grades.forEach((grade) => {
                const option = document.createElement('option');
                option.value = grade;
                option.textContent = grade;
                gradeSelect.appendChild(option);
            });
        })
        .catch((error) => console.error('Error fetching grades:', error));

    // Populate chapters dynamically when a grade is selected
    gradeSelect.addEventListener('change', async (event) => {
        const grade = event.target.value;
        if (!grade) return;

        try {
            const response = await fetch('/get_chapters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ grade }),
            });

            const chapters = await response.json();
            chapterSelect.innerHTML = '<option value="" disabled selected>Select Chapter</option>';
            chapters.forEach((chapter) => {
                const option = document.createElement('option');
                option.value = chapter;
                option.textContent = chapter;
                chapterSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching chapters:', error);
        }
    });

    // Handle question submission and display
    selectionForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const grade = gradeSelect.value;
        const chapter = chapterSelect.value;

        if (!grade || !chapter) {
            alert('Please select both grade and chapter.');
            return;
        }

        try {
            const response = await fetch('/get_question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ grade, chapter }),
            });

            const data = await response.json();
            if (data.error) {
                alert(data.error);
            } else {
                questionType.textContent = `Question Type: ${data.type}`;
                questionText.textContent = data.question;
                questionSection.style.display = 'block';
                feedbackSection.style.display = 'none';
                answerInput.value = ''; // Reset the answer input field
            }
        } catch (error) {
            console.error('Error fetching question:', error);
        }
    });

    // Handle answer submission and display feedback
    submitAnswerBtn.addEventListener('click', async () => {
        const question = questionText.textContent;
        const answer = answerInput.value;

        if (!answer.trim()) {
            alert('Please provide an answer.');
            return;
        }

        try {
            const response = await fetch('/submit_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question, answer }),
            });

            const data = await response.json();
            if (data.error) {
                alert(data.error);
            } else {
                feedbackText.textContent = data.feedback;
                questionSection.style.display = 'none';
                feedbackSection.style.display = 'block';
            }
        } catch (error) {
            console.error('Error submitting answer:', error);
        }
    });

    // Handle fetching the next question
    nextQuestionBtn.addEventListener('click', () => {
        answerInput.value = '';
        questionSection.style.display = 'none';
        feedbackSection.style.display = 'none';
        selectionForm.dispatchEvent(new Event('submit'));
    });
});
