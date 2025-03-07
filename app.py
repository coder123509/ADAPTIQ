from flask import Flask, render_template, request, session, redirect
import json
from model_functions import AdaptiqCLI


app = Flask(__name__)
app.secret_key = "sample_key"
app.config['SESSION_TYPE'] = 'filesystem'

with open("topics.json", 'r') as file:
    topics_data = json.load(file)

model_id = "mistralai/Mistral-7B-Instruct-v0.3"
token = "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"
adaptiq_cli = AdaptiqCLI(model_id, token, topics_data)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/select_topic', methods=['GET'])
def select_topic():
    return render_template('select_topic.html', topics_data=topics_data)

@app.route('/generate_question', methods=['GET', 'POST'])
def send_question():
    if request.method == 'POST':
        grade = request.form.get("grade")
        subject = request.form.get("subject")
        topic = request.form.get("topic")

        if grade:
            session['grade'] = grade
            session['subject'] = subject
            session['topic'] = topic
            session['subtopics_to_test'] = list(adaptiq_cli.topics[session['grade']][session['topic']].keys())

        subtopics = session['subtopics_to_test']

        if subtopics:
            current_subtopic = subtopics[0]

            question = adaptiq_cli.generate_question(current_subtopic, "descriptive", "Easy", session['grade'])

            session['current_question'] = question
            session['current_subtopic'] = current_subtopic

            return render_template('generate_question.html',
                                    topic=topic,
                                    question=question,
                                    current_subtopic=current_subtopic)
        else:
            return redirect('/profile')

    return render_template('generate_question.html')


@app.route('/generate_feedback', methods=['GET', 'POST'])
def generate_feedback():
    if request.method == 'POST':
        answer = request.form.get("answer")
        question = session.get('current_question')
        current_subtopic = session.get('current_subtopic')
        topic = request.form.get('topic')

        if answer and question:
            feedback = adaptiq_cli.analyze_answer(question, answer)
            adaptiq_cli.test_student(current_subtopic, question, answer, feedback)

            subtopics = session['subtopics_to_test']

            if "wrong" in feedback:
                temp = adaptiq_cli.backtrack(current_subtopic)
                session['subtopics_to_test'] = temp + subtopics[1:]
            
            else:
                session['subtopics_to_test'] = subtopics[1:]

            assessment_complete = not session['subtopics_to_test']

            if session['subtopics_to_test']:
                next_subtopic = session['subtopics_to_test'][0]
                next_question = adaptiq_cli.generate_question(next_subtopic, "descriptive", "Easy", session['grade'])

                session['current_question'] = next_question
                session['current_subtopic'] = next_subtopic

                return render_template('generate_feedback.html',
                                       topic=topic,
                                       question=question, feedback=feedback,
                                       current_subtopic=current_subtopic,
                                       assessment_complete=assessment_complete,
                                       next_question=next_question)

            return render_template('generate_feedback.html',
                                   topic=topic,
                                   question=question, feedback=feedback,
                                   current_subtopic=current_subtopic,
                                   assessment_complete=assessment_complete)

    return render_template('generate_feedback.html')


@app.route('/profile')
def profile():
    performance_data = adaptiq_cli.student_data.get("performance", [])
    
    topics_to_improve = {entry["topic"] for entry in performance_data if entry["feedback"] == 0}
    topics_done_well = {entry["topic"] for entry in performance_data if entry["feedback"] == 1}

    total_topics = len(performance_data)
    correct_topics = len(topics_done_well)
    accuracy = (correct_topics / total_topics * 100) if total_topics > 0 else 0

    return render_template(
        'profile.html',
        topics_to_improve=topics_to_improve,
        topics_done_well=topics_done_well,
        total_topics=total_topics,
        correct_topics=correct_topics,
        accuracy=accuracy
    )


if __name__ == '__main__':
    app.run(debug=True)
