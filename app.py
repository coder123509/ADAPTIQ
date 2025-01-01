from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient
import random

app = Flask(__name__)

# Hugging Face API setup
model_id = "google/gemma-2-2b-it"  # Replace with your model ID
token = "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"  # Replace with your token
client = InferenceClient(model=model_id, token=token)

# Topics structure with prerequisite links and difficulty levels
topics = {
    "Grade 10": {
        "Light": {
            "Behavior of light": {
                "Regular reflection": {},
                "Image formation": {}
            },
            "Reflection laws": {
                "Law 1": {},
                "Law 2": {}
            }
        },
        "Electricity": {
            "Electric current and circuits": {},
            "Electric Potential and Potential difference": {},
            "Ohm's Law": {},
            "Resistance": {},
            "Heating effect of electric current": {}
        },
        "Electromagnetism": {
            "Magnetism": {},
            "Electricity": {}
        }
    },
    "Grade 9": {
        "Sound": {
            "Sound Production": {},
            "Frequency": {},
            "Amplitude": {},
            "Hearing": {}
        },
        "Work and Energy": {
            "Force and Laws of Motion": {},
            "Motion": {}
        },
        "Gravitation": {
            "Force and Laws of Motion": {},
            "Pressure": {}
        },
        "Force and Laws of Motion": {
            "Force": {},
            "Motion": {}
        },
        "Motion": {
            "Speed": {},
            "Velocity": {},
            "Acceleration": {}
        }
    }
}

# Store user state and performance
user_state = {
    "grade": None,
    "current_topic": None,
    "previous_topic": None,
    "question_history": [],
    "performance": [],
    "asked_questions": {},  # Track questions asked per topic
    "current_difficulty": "easy"  # Track current difficulty level
}


# Helper function: Generate a question with difficulty level
def generate_question(topic, question_type, difficulty):
    prompt = f"You are a physics teacher testing core conceptual understanding of a student. Generate a standard {question_type} question for the topic: {topic} at {difficulty} difficulty level, without including the answer."
    try:
        response = client.text_generation(prompt, max_new_tokens=200)
        if isinstance(response, dict):
            return response.get('generated_text', 'No question generated.')
        elif isinstance(response, str):
            return response
    except Exception as e:
        return f"Error generating question: {str(e)}"
    return 'No question generated.'

# Helper function: Analyze answer
def analyze_answer(question, answer):
    prompt = f"Evaluate the following answer: \nQuestion: {question}\nAnswer: {answer}\nProvide feedback and correctness (correct/incorrect)."
    try:
        response = client.text_generation(prompt, max_new_tokens=200)
        if isinstance(response, dict):
            return response.get('generated_text', 'Unable to evaluate answer.').strip()
        elif isinstance(response, str):
            return response.strip()
    except Exception as e:
        return f"Error analyzing answer: {str(e)}"
    return 'Unable to evaluate answer.'

# Route: Home page
@app.route('/')
def home():
    grades = list(topics.keys())
    return render_template('index.html', grades=grades)

# Route: Get chapters for a selected grade
@app.route('/get_chapters', methods=['POST'])
def get_chapters():
    data = request.json
    grade = data.get('grade')
    if not grade or grade not in topics:
        return jsonify({'error': 'Invalid grade selected.'}), 400
    chapters = list(topics[grade].keys())
    return jsonify(chapters)

# Route: Start a test
@app.route('/start_test', methods=['POST'])
def start_test():
    data = request.json
    grade = data.get('grade')
    chapter = data.get('chapter')

    if not grade or not chapter:
        return jsonify({'error': 'Grade and chapter are required.'}), 400
    if grade not in topics or chapter not in topics[grade]:
        return jsonify({'error': 'Invalid grade or chapter.'}), 400

    user_state["grade"] = grade
    user_state["current_topic"] = chapter
    user_state["previous_topic"] = None
    user_state["question_history"] = []
    user_state["performance"] = []
    user_state["asked_questions"] = {}
    user_state["current_difficulty"] = "easy"

    # Generate the first easy question for the selected topic
    question = generate_question(chapter, "MCQ", difficulty="easy")
    user_state["asked_questions"].setdefault(chapter, []).append(question)
    user_state["question_history"].append({"topic": chapter, "question": question})

    return jsonify({'message': f"Test started for chapter: {chapter}", "question": question, "difficulty": "easy"})
# Helper function: Get prerequisites for a topic
def get_prerequisites(chapter):
    grade = user_state["grade"]
    if grade in topics and chapter in topics[grade]:
        return list(topics[grade][chapter].keys())
    return []

# Helper function: Get the next topic in prerequisites
def get_next_prerequisite(chapter):
    prerequisites = get_prerequisites(chapter)
    for prereq in prerequisites:
        if prereq not in user_state["asked_questions"]:
            return prereq
        deeper_prereq = get_next_prerequisite(prereq)
        if deeper_prereq:
            return deeper_prereq
    return None
# Route: Submit answer
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    data = request.json
    last_answer = data.get('answer')

    # Validate input
    if not last_answer:
        return jsonify({'error': 'Answer is required.'}), 400

    # Check if there is a question to analyze
    if not user_state["question_history"]:
        return jsonify({'error': 'No question to analyze.'}), 400

    # Get the last question and analyze the answer
    last_question = user_state["question_history"][-1]
    feedback = analyze_answer(last_question['question'], last_answer)

    # Store performance data
    user_state["performance"].append({
        "question": last_question['question'],
        "answer": last_answer,
        "feedback": feedback
    })

    response = {
        "feedback": feedback,
        "correctness": "correct" if "correct" in feedback.lower() else "incorrect"
    }

    # If the answer is incorrect, backtrack to prerequisites
    if "incorrect" in feedback.lower():
        next_topic = get_next_prerequisite(user_state["current_topic"])
        if next_topic:
            user_state["previous_topic"] = user_state["current_topic"]
            user_state["current_topic"] = next_topic
            user_state["current_difficulty"] = "easy"

            # Generate a question for the new topic
            question = generate_question(next_topic, "MCQ", difficulty="easy")
            user_state["asked_questions"].setdefault(next_topic, []).append(question)
            user_state["question_history"].append({"topic": next_topic, "question": question})

            response.update({
                "message": f"Backtracking... Current topic: {user_state['current_topic']}, Previous topic: {user_state['previous_topic']}",
                "next_question": question,
                "next_topic": next_topic,
                "difficulty": "easy"
            })
            return jsonify(response)

    # Adjust difficulty for the next question
    if user_state["current_difficulty"] == "easy":
        user_state["current_difficulty"] = "medium"
    elif user_state["current_difficulty"] == "medium":
        user_state["current_difficulty"] = "hard"

    return jsonify(response)
# Route: Get the next question
@app.route('/next_question', methods=['POST'])
def next_question():
    if not user_state["current_topic"]:
        return jsonify({"error": "No topic selected. Please start a test first."}), 400

    # Generate the next question for the current topic based on difficulty level
    topic = user_state["current_topic"]
    difficulty = "easy" if len(user_state["question_history"]) == 0 else ("medium" if len(user_state["question_history"]) == 1 else "hard")

    # Ensure no repeated questions
    while True:
        question = generate_question(topic, random.choice(["MCQ", "descriptive"]), difficulty)
        if question not in user_state["asked_questions"].get(topic, []):
            break

    # Track the asked question
    if topic not in user_state["asked_questions"]:
        user_state["asked_questions"][topic] = []
    user_state["asked_questions"][topic].append(question)

    user_state["question_history"].append({"topic": topic, "question": question})
    return jsonify({"question": question, "topic": topic})

# Route: End the test
@app.route('/end_test', methods=['POST'])
def end_test():
    return jsonify({"performance": user_state["performance"], "message": "Test ended."})

if __name__ == "__main__":
    app.run(debug=True)
