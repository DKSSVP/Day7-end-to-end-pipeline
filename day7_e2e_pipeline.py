import os
import json
import requests

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SHEETDB_API_URL = os.getenv("SHEETDB_API_URL")

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


candidate_resume = """
Rahul Kumar
Email: rahul.kumar@example.com
Phone: +91 9123456789
Location: Hyderabad, Telangana

Rahul Kumar is a GenAI Engineer with 2 years of experience
in developing AI-powered applications.

Skills:
Python, Java, Prompt Engineering, REST APIs, Git, SQL

Education:
B.Tech in Computer Science

Availability:
Immediate
"""

extraction_prompt = f"""
Extract the candidate information from the resume below.

Return one valid JSON object with these fields:
Name
Email
Role
Skills
Availability

Rules:
- Return JSON only.
- Do not use Markdown code fences.
- Do not add explanations.
- Use only information available in the resume.
- Do not invent information.

Resume:
{candidate_resume}
"""

def extract_profile_to_json(resume_text):
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": "You are a candidate profile extraction assistant. Return valid JSON only."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ]
    )

    raw_output = response.choices[0].message.content.strip()

    return raw_output

def validate_extracted_json(raw_output):
    try:
        return json.loads(raw_output)

    except json.JSONDecodeError as error:
        print("Invalid JSON returned by the LLM.")
        print("Error:", error)
        return None

def push_to_sheetdb(candidate_data):
    payload = {
        "data": [candidate_data]
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    response = requests.post(
        SHEETDB_API_URL,
        json=payload,
        headers=headers,
        timeout=10
    )

    return response

print("----- Candidate Extraction -----")

raw_output = extract_profile_to_json(candidate_resume)

print("Raw LLM Output:")
print(raw_output)

candidate_data = validate_extracted_json(raw_output)

if candidate_data is not None:
    print("----- Valid Candidate JSON -----")
    print(json.dumps(candidate_data, indent=2))

    print("----- SheetDB Persistence -----")

    response = push_to_sheetdb(candidate_data)

    print("HTTP Status Code:", response.status_code)

    if response.status_code == 201:
        print("Candidate record added successfully.")
    else:
        print("SheetDB request failed.")
        print("Response:", response.text)
