from google import genai
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv
load_dotenv()

class Activity(BaseModel):
    activityName : str
    activityDescription : str
    activityObjective : str
    activityType: str

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Template for the LLM prompt
PROMPT_TEMPLATE = """
You are an expert instructional designer.

Your task is to generate a list of learning activities for a course submodule. The user will provide the submodule name, description, and optionally a set of instructions and preferred activity types (like Lecture, Quiz, Assessment, etc.).

### Input:
- Submodule Name: {submodule_name}
- Submodule Description: {submodule_description}
- Preferred Activity Types: {activity_types}
- User Instructions (optional): {user_instructions}

### If no user instructions are provided, follow these general guidelines:
- Make activities clear, beginner-friendly, and well-aligned with the submodule’s goal.
- Cover a mix of conceptual understanding and applied thinking.
- Ensure activities are engaging and useful for learners.
- Avoid duplication across types.
- There can be multiple activities of single type so as to best align with submodule's goal.

### Output Format:
Return the result strictly as a **JSON array** of activity objects. Each object should include:
- "activityName": Title of the activity
- "activityDescription": A short paragraph describing what the activity is
- "activityObjective": A specific learning objective or outcome for the activity
- "activityType": One of the types provided (Lecture, Quiz, Assessment, Reading Material, Lab)

Now, generate the activity list based on the inputs provided.
Only return the JSON array as the output.
"""

def build_prompt(submodule_name, submodule_description, activity_types, user_instructions=None):
    return PROMPT_TEMPLATE.format(
        submodule_name=submodule_name,
        submodule_description=submodule_description,
        activity_types=activity_types,
        user_instructions=user_instructions or "None provided"
    )

def validate_activities_json(activities_json):
    """
    Ensures the returned JSON is a list of activity dictionaries
    with all required fields.
    """
    required_fields = {"activityName", "activityDescription", "activityObjective", "activityType"}

    if not isinstance(activities_json, list):
        return False, "Expected a list of activities."

    for i, activity in enumerate(activities_json):
        if not isinstance(activity, dict):
            return False, f"Item {i} is not a dictionary."
        missing = required_fields - set(activity.keys())
        if missing:
            return False, f"Item {i} is missing fields: {missing}"

    return True, "Valid JSON format."

def generate_activities(submodule_name, submodule_description, activity_types, user_instructions=None):
    prompt = build_prompt(submodule_name, submodule_description, activity_types, user_instructions)
    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": list[Activity],
                    },
                )
    raw_text = response.text.strip()
    print(raw_text)
    # Try to extract JSON
    try:
        # Clean up response if wrapped in code block
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()
        
        activities = json.loads(raw_text)
        valid, message = validate_activities_json(activities)
        if not valid:
            raise ValueError(message)
        return activities
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except Exception as ex:
        raise ValueError(f"Validation error: {ex}")
    
def rebuild_activity_list(
    existing_activities: list[dict],
    submodule_name: str,
    submodule_description: str,
    user_suggestion: str
) -> list[dict]:
    """
    Regenerates or modifies a list of learning activities based on user feedback or suggestions.
    """

    prompt = f"""
You are an expert instructional designer.

You are given a list of learning activities for a course submodule. The user has now requested changes or improvements.

### Submodule:
- Name: {submodule_name}
- Description: {submodule_description}

### Existing Activities:
{json.dumps(existing_activities, indent=2)}

### User Suggestion:
"{user_suggestion}"

### Instructions:
- Based on the user's suggestion, modify or regenerate activities.
- You may remove, rewrite, or add activities as needed.
- Keep the output structured and clear.
- Adjust the number of activities if the user has asked for it.
- Do not repeat activities unless explicitly requested.
- Only output the new or modified list of activities in the format below.

### Output JSON Format:
Return a JSON array of activity objects with the following fields:
- "activityName"
- "activityDescription"
- "activityObjective"
- "activityType"

Return only the updated JSON array. No extra explanation.
"""

    response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": list[Activity],
                    },
                )
    raw_text = response.text.strip()

    try:
        if raw_text.startswith("```json"):
            raw_text = raw_text.strip("```json").strip("```").strip()

        activities = json.loads(raw_text)
        valid, message = validate_activities_json(activities)
        if not valid:
            raise ValueError(message)

        return activities

    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}")
    except Exception as ex:
        raise ValueError(f"Validation error: {ex}")
