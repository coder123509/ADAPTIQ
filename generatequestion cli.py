from huggingface_hub import InferenceClient
import random

class AdaptiqCLI:
    def _init_(self, model_id, token):
        self.client = InferenceClient(model=model_id, token=token)
        self.topics = {
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

    def generate_question(self, topic, question_type):
        prompt = f"Generate a {question_type} question for the topic: {topic}"
        response = self.client.text_generation(prompt, max_new_tokens=100)
        if isinstance(response, dict):
            return response.get('generated_text', 'No question generated.')
        elif isinstance(response, str):
            return response
        else:
            return 'No question generated.'

    def analyze_answer(self, question, answer):
        prompt = f"Evaluate the following answer: \nQuestion: {question}\nAnswer: {answer}\nProvide feedback and correctness (correct/incorrect)."
        response = self.client.text_generation(prompt, max_new_tokens=100)
        if isinstance(response, dict):
            return response.get('generated_text', 'Unable to evaluate answer.').strip()
        elif isinstance(response, str):
            return response.strip()
        else:
            return 'Unable to evaluate answer.'

    def test_student(self, topic):
        question_type = random.choice(["MCQ", "descriptive"])
        question = self.generate_question(topic, question_type)
        print(f"{question_type} Question: {question}")
        answer = input("Your Answer: ")
        feedback = self.analyze_answer(question, answer)
        print(f"Feedback: {feedback}")
        return "correct" in feedback.lower()

    def backtrack(self, topic):
        print(f"Testing prerequisites for topic: {topic}")
        for subtopic, details in self.topics.get(topic, {}).items():
            print(f"Subtopic: {subtopic}")
            if not self.test_student(subtopic):
                self.backtrack(subtopic)

    def start_testing(self):
        print("Welcome to Adaptiq CLI")
        grade = input("Enter the grade (e.g., Grade 10): ").strip()
        if grade in self.topics:
            chapter = input("Enter the chapter (e.g., Light): ").strip()
            if chapter in self.topics[grade]:
                print(f"Starting testing for chapter: {chapter}")
                for subtopic in self.topics[grade][chapter]:
                    if not self.test_student(subtopic):
                        self.backtrack(subtopic)
            else:
                print("Chapter not found.")
        else:
            print("Grade not found.")

if _name_ == "_main_":
    model_id = "google/gemma-2-2b-it"  # Replace with your model ID
    token = "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"  # Replace with your Hugging Face token
    adaptiq_cli = AdaptiqCLI(model_id, token)
    adaptiq_cli.start_testing()
 this works really well check it once (cli)
