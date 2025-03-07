document.addEventListener("DOMContentLoaded", function () {
    // DOM elements
    const gradeSelect = document.getElementById("grade");
    const topicSelect = document.getElementById("topic");
    const submitBtn = document.getElementById("submit-btn");

    // Parse the topicsData from the <script> tag
    const topicsData = JSON.parse(document.getElementById("topics-data").textContent);

    // Populate the grade dropdown with grades from topicsData
    Object.keys(topicsData.Topics).forEach(grade => {
        const option = document.createElement("option");
        option.value = grade;
        option.textContent = grade;
        gradeSelect.appendChild(option);
    });

    // Enable gradeSelect after population
    gradeSelect.disabled = false;

    // On grade change, populate the topic dropdown based on the selected grade
    gradeSelect.addEventListener("change", function () {
        const selectedGrade = gradeSelect.value;

        // Reset topic dropdown and button state
        topicSelect.innerHTML = "<option value=''>Select Topic</option>";  // Reset topic options
        topicSelect.disabled = true;  // Disable topic dropdown until grade is selected
        submitBtn.disabled = true;  // Disable submit button until topic is selected

        // Populate topics if a valid grade is selected
        if (selectedGrade && topicsData.Topics[selectedGrade]) {
            const topics = Object.keys(topicsData.Topics[selectedGrade]);

            topics.forEach(topic => {
                const option = document.createElement("option");
                option.value = topic;
                option.textContent = topic;
                topicSelect.appendChild(option);
            });

            // Enable the topic dropdown
            topicSelect.disabled = false;
        }
    });

    // On topic change, enable the submit button
    topicSelect.addEventListener("change", function () {
        submitBtn.disabled = !topicSelect.value;  // Enable if a topic is selected
    });
});