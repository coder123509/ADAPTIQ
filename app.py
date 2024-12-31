from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient
import random

app = Flask(__name__)

# Hugging Face API setup
model_id = "google/gemma-2-2b-it"  # Replace with your model ID
token = "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"  # Replace with your token
client = InferenceClient(model=model_id, token=token)

# Topics structure with prerequisite links
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
            "Electricity quantities": {}
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
            "Speed": {}
        }
    }
}

# Store user state and performance
user_state = {
    "current_topic": None,
    "question_history": [],
    "performance": []
}

# Helper function: Generate a question
def generate_question(topic, question_type):
    prompt = f"Generate a standard {question_type} question for the topic: {topic}, without including the answer."
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

    user_state["current_topic"] = chapter
    user_state["question_history"] = []
    user_state["performance"] = []
    return jsonify({'message': f"Test started for chapter: {chapter}"})


def get_prerequisites(grade, chapter):
    # Ensure we are getting the correct subtopics or prerequisites for the given chapter
    if grade in topics and chapter in topics[grade]:
        subtopics = list(topics[grade][chapter].keys())
        if subtopics:
            return subtopics
    return []

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

    # Prepare response
    response = {
        "feedback": feedback,
        "correctness": "correct" if "correct" in feedback.lower() else "incorrect"
    }

    # Backtrack if the answer is incorrect
    if "incorrect" in feedback.lower():
        grade = data.get('grade')
        chapter = data.get('chapter')

        if grade and chapter:
            # Get prerequisites (subtopics) for the current chapter
            prerequisites = get_prerequisites(grade, chapter)
            if prerequisites:
                next_topic = prerequisites[0]  # You can choose to backtrack to any prerequisite
                user_state["current_topic"] = next_topic  # Update the current topic
                question = generate_question(next_topic, random.choice(["MCQ", "descriptive"]))
                user_state["question_history"].append({"topic": next_topic, "question": question})
                response.update({
                    "next_question": question,
                    "next_topic": next_topic
                })
                return jsonify(response)

    # Generate a new question if no backtracking is required
    topic = user_state["current_topic"]
    question = generate_question(topic, random.choice(["MCQ", "descriptive"]))
    user_state["question_history"].append({"topic": topic, "question": question})
    response.update({"next_question": question, "next_topic": topic})
    return jsonify(response)

# Route: Get the next question
@app.route('/next_question', methods=['POST'])
def next_question():
    data = request.json
    last_answer = data.get('last_answer', None)

    # If the user has answered a question, analyze it
    if user_state["question_history"]:
        last_question = user_state["question_history"][-1]
        feedback = analyze_answer(last_question['question'], last_answer)
        user_state["performance"].append({
            "question": last_question['question'],
            "answer": last_answer,
            "feedback": feedback
        })
        if "incorrect" in feedback.lower():
            # Backtrack to prerequisite topic if available
            prerequisites = list(topics[user_state["current_topic"]].keys())
            if prerequisites:
                next_topic = prerequisites[0]
                user_state["current_topic"] = next_topic
                question = generate_question(next_topic, random.choice(["MCQ", "descriptive"]))
                user_state["question_history"].append({"topic": next_topic, "question": question})
                return jsonify({"question": question, "topic": next_topic})

    # Generate the next question for the current topic
    topic = user_state["current_topic"]
    question = generate_question(topic, random.choice(["MCQ", "descriptive"]))
    user_state["question_history"].append({"topic": topic, "question": question})
    return jsonify({"question": question, "topic": topic})

# Route: End the test
@app.route('/end_test', methods=['POST'])
def end_test():
    return jsonify({"performance": user_state["performance"], "message": "Test ended."})

if __name__ == "__main__":
    app.run(debug=True)
