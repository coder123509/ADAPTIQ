from huggingface_hub import InferenceClient
import random

class AdaptiqCLI:
    def __init__(self, model_id, token):
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

        self.student_data = {
            "name": None,
            "grade": None,
            "chapter": None,
            "performance": []
        }

    def generate_question(self, topic, question_type):
        prompt = f"Generate a {question_type} question for the topic: {topic}"
        response = self.client.text_generation(prompt, max_new_tokens=200)
        if isinstance(response, dict):
            return response.get('generated_text', 'No question generated.')
        elif isinstance(response, str):
            return response
        else:
            return 'No question generated.'

    def analyze_answer(self, question, answer):
        prompt = f"Evaluate the following answer: \nQuestion: {question}\nAnswer: {answer}\nProvide feedback and correctness (correct/incorrect)."
        response = self.client.text_generation(prompt, max_new_tokens=200)
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

        # Ask for the user's answer first, then evaluate
        answer = input("Your Answer: ")

        # Only after the user types the answer, evaluate it
        feedback = self.analyze_answer(question, answer)
        print(f"Feedback: {feedback}")

        # Track the performance
        performance = "correct" if "correct" in feedback.lower() else "incorrect"
        self.student_data["performance"].append({"topic": topic, "answer": answer, "feedback": performance})

        # Return whether the answer was correct or incorrect
        return performance == "correct"

    def backtrack(self, topic):
        print(f"Testing prerequisites for topic: {topic}")
        for subtopic, details in self.topics.get(topic, {}).items():
            print(f"Subtopic: {subtopic}")
            if not self.test_student(subtopic):
                self.backtrack(subtopic)

    def display_dashboard(self):
        print("\n--- Profile Dashboard ---")
        print(f"Name: {self.student_data['name']}")
        print(f"Grade: {self.student_data['grade']}")
        print(f"Chapter: {self.student_data['chapter']}")
        print("\nPerformance Summary:")
        
        total_questions = len(self.student_data["performance"])
        correct_answers = sum(1 for p in self.student_data["performance"] if p["feedback"] == "correct")
        
        print(f"Total Questions Answered: {total_questions}")
        print(f"Correct Answers: {correct_answers}")
        print(f"Accuracy: {correct_answers / total_questions * 100:.2f}%")
        
        # Optionally, print feedback for each question
        print("\nDetailed Feedback:")
        for p in self.student_data["performance"]:
            print(f"Topic: {p['topic']}, Your Answer: {p['answer']}, Feedback: {p['feedback']}")

    def start_testing(self):
        print("Welcome to Adaptiq CLI")

        # Collect profile information
        self.student_data["name"] = input("Enter your name: ").strip()
        self.student_data["grade"] = input("Enter the grade (e.g., Grade 10): ").strip()

        if self.student_data["grade"] in self.topics:
            self.student_data["chapter"] = input("Enter the chapter (e.g., Light): ").strip()
            if self.student_data["chapter"] in self.topics[self.student_data["grade"]]:
                print(f"Starting testing for chapter: {self.student_data['chapter']}")

                # Loop through the topics and ask only one question at a time
                while True:
                    for subtopic in self.topics[self.student_data["grade"]][self.student_data["chapter"]]:
                        if not self.test_student(subtopic):
                            self.backtrack(subtopic)

                    # Ask if the user wants to continue or stop
                    continue_test = input("Do you want to continue? (y/n): ").strip().lower()
                    if continue_test != 'y':
                        print("Ending the test.")
                        self.display_dashboard()
                        break
            else:
                print("Chapter not found.")
        else:
            print("Grade not found.")

if __name__ == "__main__":
    model_id = "google/gemma-2-2b-it"  # Replace with your model ID
    token = "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"  # Replace with your Hugging Face token
    adaptiq_cli = AdaptiqCLI(model_id, token)
    adaptiq_cli.start_testing()
