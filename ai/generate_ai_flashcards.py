from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = "https://models.inference.ai.azure.com"
model_name = "Llama-3.3-70B-Instruct"
token = os.getenv("GITHUB_TOKEN")

# def generate_flashcards(topic, quantity, exam_board):
#     if exam_board != "":
#         prompt = f"Generate {quantity} thorough and detailed exam styled flashcard questions for me on this: '{topic}', only give details on what is mentioned, be specific to {exam_board} exam board. Try to keep answers medium length, that is effective for students to memorize. Return only a Python 2D list where each sublist contains a question and its answer, with no extra text."
#     else:
#         prompt = f"Generate {quantity} thorough and detailed exam styled flashcard questions for me on this: '{topic}'. Try to keep answers medium length, that is effective for students to memorize. Return only a Python 2D list where each sublist contains a question and its answer, with no extra text."

#     response = client.chat.completions.create(
#         model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
#         messages=[{"role": "user", "content": prompt}],
#     )
#     flashcards_str = response.choices[0].message.content
#     # Convert the string response to a Python list
#     flashcards = eval(flashcards_str)  # Note: eval can be dangerous, use json.loads if possible
#     return flashcards

def generate_flashcards_api(topic, quantity, exam_board):
    """
    Generates flashcards using OpenAI's GPT model.
    
    Args:
        topic (str): The topic for the flashcards.
        quantity (int): The number of flashcards to generate.
        exam_board (str): The exam board (optional).
    
    Returns:
        list: A 2D list of flashcards, where each sublist contains a question and its answer.
    """
    
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )


    if exam_board:
        response = client.complete(
            messages=[
                SystemMessage("You are an AI Flashcard Generator."),
                UserMessage(f"Generate {quantity} thorough and detailed exam-styled flashcard questions on the topic: '{topic}'. Be specific to the {exam_board} exam board. Keep answers medium-length for effective memorization. Return only a Python 2D list where each sublist contains a question and its answer, with no extra text."),
            ],
            temperature=1.0,
            top_p=1.0,
            model=model_name
        )
    else:
        response = client.complete(
            messages=[
                SystemMessage("You are an AI Flashcard Generator."),
                UserMessage(f"Generate {quantity} thorough and detailed exam-styled flashcard questions on the topic: '{topic}'. Keep answers medium-length for effective memorization. Return only a Python 2D list where each sublist contains a question and its answer, with no extra text."),
            ],
            temperature=1.0,
            top_p=1.0,
            model=model_name
        )

    # Extract the response content
    flashcards_str = response.choices[0].message.content

    # Convert the string response to a Python list
    try:
        flashcards = eval(flashcards_str)  # Note: eval can be dangerous; use json.loads if possible
    except Exception as e:
        print(f"Error parsing flashcards: {e}")
        flashcards = []

    print(flashcards)

    return flashcards