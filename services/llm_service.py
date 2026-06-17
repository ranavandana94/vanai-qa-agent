import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

for m in genai.list_models():
    print(m.name)

model = genai.GenerativeModel("gemini-3-flash-preview")
def analyze_requirement(requirement: str):

    with open(
        "prompts/qa_review_prompt.txt",
        "r"
    ) as file:
        prompt_template = file.read()

    prompt = prompt_template.format(
        requirement=requirement
    )

    response = model.generate_content(prompt)   
    
    return response.text