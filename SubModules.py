from google import genai
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, HTTPException
import os
import json

# Load Gemini API key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

# FastAPI app
app = FastAPI()

# Submodule schema
class Submodule(BaseModel):
    submoduleName: str
    submoduleDescription: str

# ---------- Prompt Templates ----------

SUBMODULE_PROMPT_TEMPLATE = """
You are a highly skilled instructional designer.

Your task is to generate a list of submodules for a course module. You will be given the **course outline**, **module name**, **module description**, and **number of credits** for the module.

Each submodule should be:
- A logically scoped unit of learning under the module.
- Clearly named.
- Accompanied by a short beginner-friendly description (2–3 lines).
- Proportional in quantity and depth to the credit count (i.e., more credits = more submodules or deeper concepts).

### Input:
Course Outline: {course_outline}
Module Name: {module_name}
Module Description: {module_description}
Credits for the Module: {credits}

### Output Format:
Return the result as a JSON array of objects with:
- "submoduleName"
- "submoduleDescription"

Only return the JSON array. Do not include any explanation or commentary.
"""

def build_submodule_prompt(course_outline, module_name, module_description, credits):
    return SUBMODULE_PROMPT_TEMPLATE.format(
        course_outline=course_outline,
        module_name=module_name,
        module_description=module_description,
        credits=credits
    )

def build_regeneration_prompt(existing_submodules, user_instruction):
    return f"""
You are an expert instructional designer.

You are given an existing list of submodules. Your task is to regenerate the submodules based on new user instructions. Either improve, modify, or completely replace them depending on what the user asks.

### Existing Submodules:
{submodules_to_bullets(existing_submodules)}

### User Instruction:
{user_instruction}

### Output Format:
Return the result as a JSON array of objects with:
- "submoduleName"
- "submoduleDescription"

Only return the JSON array. Do not include any explanation or commentary.
"""

def submodules_to_bullets(submodules):
    bullets = ""
    for sub in submodules:
        bullets += f"- {sub['submoduleName']}: {sub['submoduleDescription']}\n"
    return bullets

# ---------- Validation ----------

def validate_submodules_json(submodules_json):
    required_fields = {"submoduleName", "submoduleDescription"}
    if not isinstance(submodules_json, list):
        return False, "Expected a list of submodules."

    for i, sub in enumerate(submodules_json):
        if not isinstance(sub, dict):
            return False, f"Item {i} is not a dictionary."
        missing = required_fields - set(sub.keys())
        if missing:
            return False, f"Item {i} is missing fields: {missing}"

    return True, "Valid JSON format."

# ---------- Generation ----------

def generate_submodules(course_outline, module_name, module_description, credits):
    prompt = build_submodule_prompt(course_outline, module_name, module_description, credits)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Submodule],
        },
    )
    raw_text = response.text.strip()

    try:
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
        submodules = json.loads(raw_text)
        valid, message = validate_submodules_json(submodules)
        if not valid:
            raise ValueError(message)
        return submodules
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing failed: {e}")
    except Exception as ex:
        raise ValueError(f"Validation error: {ex}")

def regenerate_submodules_with_instruction(existing_submodules, user_instruction):
    prompt = build_regeneration_prompt(existing_submodules, user_instruction)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": list[Submodule],
        },
    )
    raw_text = response.text.strip()

    try:
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
        new_submodules = json.loads(raw_text)
        valid, message = validate_submodules_json(new_submodules)
        if not valid:
            raise ValueError(message)
        return new_submodules
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON parsing failed: {e}")
    except Exception as ex:
        raise ValueError(f"Validation error: {ex}")

# ---------- FastAPI Routes ----------

class SubmoduleInput(BaseModel):
    course_outline: str
    module_name: str
    module_description: str
    credits: int

class RegenerateInput(BaseModel):
    existing_submodules: List[Submodule]
    user_instruction: str

@app.post("/generate-submodules")
def api_generate_submodules(input_data: SubmoduleInput):
    try:
        submodules = generate_submodules(
            course_outline=input_data.course_outline,
            module_name=input_data.module_name,
            module_description=input_data.module_description,
            credits=input_data.credits
        )
        return {"submodules": submodules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/regenerate-submodules")
def api_regenerate_submodules(input_data: RegenerateInput):
    try:
        submodules = regenerate_submodules_with_instruction(
            existing_submodules=[s.dict() for s in input_data.existing_submodules],
            user_instruction=input_data.user_instruction
        )
        return {"submodules": submodules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- CLI Runner ----------

def main():
    # Step 1: Initial generation
    course_outline = "This course introduces machine learning foundations, including supervised and unsupervised learning, evaluation metrics, and practical model training using Python."
    module_name = "Supervised Learning"
    module_description = "This module covers classification and regression techniques using decision trees, logistic regression, and support vector machines."
    credits = 3

    try:
        submodules = generate_submodules(course_outline, module_name, module_description, credits)

        # Save to file
        with open("submodules.json", "w") as f:
            json.dump(submodules, f, indent=2)

        print(json.dumps(submodules, indent=2))

        # Optional: Simulate user instruction for regeneration
        user_instruction = "Make the submodules more project-based and interactive."
        regenerated = regenerate_submodules_with_instruction(submodules, user_instruction)

        # Save and print regenerated version
        with open("submodules_regenerated.json", "w") as f:
            json.dump(regenerated, f, indent=2)

        print("\nRegenerated based on user instruction:")
        print(json.dumps(regenerated, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    main()
