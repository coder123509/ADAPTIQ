import json
from huggingface_hub import InferenceClient
import time

class AdaptiqCLI:
    def __init__(self, model_id, token, topics_dictionary):
        self.client = InferenceClient(model=model_id, token=token)
        self.topics = topics_dictionary["Topics"]
        self.student_data = {
            "name": None,
            "grade": None,
            "chapter": None,
            "performance": []
        }


    def generate_question(self, topic, question_type, difficulty, grade):
    
        prompt = f"""
            You are tasked to generate a single question for a {grade} student based on the requirements below.
            No answer or formula or other text should be provided, except the question itself.
            Word 'Question' should appear only once.
      
            Topic: {topic}
            Question type: {question_type},
            Difficulty Level: {difficulty},
            Number of questions: 1

            Format: 'Question: <generated question>'
        """
        response = self.client.text_generation(prompt, max_new_tokens=200)
        return response
    

    def analyze_answer(self, question, answer):
        prompt = f"""
        Evaluate the following answer for the question: 
        Question: {question}
        Answer: {answer}
        Provide feedback on whether the answer is correct or incorrect.
        Respond with the evaluation as a brief statement.
        Include the word 'correct' or 'wrong' in your evaluation.
        No other redundant text is allowed.
        """

        response = self.client.text_generation(prompt, max_new_tokens=200)

        return response.strip()


    def test_student(self, topic, question, answer, feedback):
        question_type = "descriptive"

        if "wrong" in feedback.lower():
            performance = 0
        else:
            performance = 1

        self.student_data["performance"].append({
            "topic": topic, "answer": answer, "feedback": performance
        })

        return performance


    def backtrack(self, target):
        queue = [self.topics]

        while queue:
            current_level = queue.pop(0)

            for topic, subtopics in current_level.items():
                if topic == target:
                    return list(subtopics.keys())
                else:
                    if isinstance(subtopics, dict): 
                        queue.append(subtopics)
        
        return []
        

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


    def start_testing(self):
        print("Welcome to Adaptiq CLI")

        self.student_data["name"] = input("Enter your name: ").strip()

        self.student_data["grade"] = input("Enter the grade (e.g., Grade 10): ").strip()
        if self.student_data["grade"] not in self.topics:
            print("Grade not found.")
            return "Error: Grade not found"
        
        self.student_data["chapter"] = input("Enter the chapter (e.g., Light): ").strip()
        if self.student_data["chapter"] not in self.topics[self.student_data["grade"]]:
            print("Chapter not found.")
            return "Error: Chapter not found"
        
        print(f"Starting testing for chapter: {self.student_data['chapter']}")

        subtopics_to_test = list(self.topics[self.student_data["grade"]][self.student_data["chapter"]].keys())
        performance_data = []

        while subtopics_to_test:
            current_subtopic = subtopics_to_test.pop(0)
            question = self.generate_question(current_subtopic, "descriptive", "Easy", "Grade 10")
            answer = input(f"\n{question}\n")
        
            # Analyze the answer and get feedback
            feedback = self.analyze_answer(question, answer)
            
            # Test the student with the question, answer, and feedback
            performance = self.test_student(current_subtopic, question, answer, feedback)
            
            performance_data.append({"subtopic": current_subtopic, "performance": performance})

            if performance == 0:
                print(f"Backtracking on {current_subtopic}...")

                next_subtopics = self.backtrack(current_subtopic)

                if next_subtopics:
                    print(f"Found subtopics for {current_subtopic}: {next_subtopics}")
                    subtopics_to_test.extend(next_subtopics)
                else:
                    print(f"No more subtopics to test for {current_subtopic}.")

            else:
                print("\nGood job! Moving on...\n")

        
        if all(item["performance"] == 1 for item in performance_data):
            print("You have successfully completed the assessment for all subtopics!")
        else:
            print("There are still some subtopics left to review.")

        continue_test = input("Do you want to continue the test? (y/n): ").strip().lower()
        if continue_test != 'y':
            print("Ending the test.")
            self.display_dashboard()
        else:
            adaptiq_cli.start_testing()



if __name__ == "__main__":
    with open ("topics.json", 'r') as file:
        topic_dictionary = json.load(file) 
    model_id = "mistralai/Mistral-7B-Instruct-v0.3"  # Replace with your model ID
    token = "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"  # Replace with your Hugging Face token
    adaptiq_cli = AdaptiqCLI(model_id, token, topic_dictionary)
    adaptiq_cli.start_testing()