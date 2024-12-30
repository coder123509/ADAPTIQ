from flask import Flask, render_template, request, jsonify
from huggingface_hub import InferenceClient
import random

app = Flask(__name__)

# Hugging Face API setup
model_id = "google/gemma-2-2b-it"  # Replace with your model ID
token = "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"  # Replace with your actual token
client = InferenceClient(model=model_id, token=token)

# Topics structure
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

# Store performance data
performance_data = []

# Helper function: Generate a question
def generate_question(topic, question_type):
    prompt = f"Generate a single {question_type} question for the topic: {topic}"
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

# Route: Start test
@app.route('/start_test', methods=['POST'])
def start_test():
    grade = request.form.get('grade')
    chapter = request.form.get('chapter')
    if not grade or not chapter:
        return "Grade and chapter are required.", 400

    # Generate question
    question_type = random.choice(["MCQ", "descriptive"])
    subtopic = random.choice(list(topics[grade][chapter].keys()))
    question = generate_question(subtopic, question_type)

    return render_template(
        'test.html',
        grade=grade,
        chapter=chapter,
        question=question,
        question_type=question_type,
        subtopic=subtopic
    )

# Route: Generate a question
@app.route('/get_question', methods=['POST'])
def get_question():
    data = request.json
    grade = data.get('grade')
    chapter = data.get('chapter')

    if not grade or not chapter:
        return jsonify({'error': 'Grade and chapter are required.'}), 400
    if grade not in topics or chapter not in topics[grade]:
        return jsonify({'error': 'Invalid grade or chapter.'}), 400

    question_type = random.choice(["MCQ", "descriptive"])
    subtopic = random.choice(list(topics[grade][chapter].keys()))
    question = generate_question(subtopic, question_type)

    return jsonify({'type': question_type, 'question': question, 'subtopic': subtopic})

# Route: Submit an answer for evaluation
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question = request.form.get('question')
    answer = request.form.get('answer')

    if not question or not answer:
        return jsonify({'error': 'Question and answer are required.'}), 400

    feedback = analyze_answer(question, answer)
    performance_data.append({'question': question, 'answer': answer, 'feedback': feedback})
    return render_template('feedback.html', feedback=feedback)

# Route: Get performance data (optional for analysis)
@app.route('/performance', methods=['GET'])
def get_performance():
    return jsonify(performance_data)

if __name__ == "__main__":
    app.run(debug=True)
