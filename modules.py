# module_genai_logic.py

import os
from google import genai
from google.genai.types import GenerateContentConfig, Content, Part
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Any
from suggestion_logic import get_stage_suggestions  # Import your suggestions logic

load_dotenv()

llmclient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class Module(BaseModel):
    module_title: str
    description: str
    module_hours: str

def generate_modules_from_outline(outline: Dict[str, Any], num_modules: int = 5) -> List[Dict]:
    prompt = f"""
You are an expert course designer. Based on the following course outline, generate a detailed list of {num_modules} logical course modules that progressively build upon each other.

COURSE OUTLINE:
{outline}

REQUIREMENTS:
- Create exactly {num_modules} modules
- Ensure logical progression from basic to advanced concepts
- Distribute content evenly across modules
- Align with the course's learning outcomes and objectives
- Consider the target audience and prerequisites

Each module should include:
- module_title: (clear, descriptive title that reflects the module's core focus)
- description: (detailed explanation of the module's content, learning goals, and what students will achieve)
- module_hours: (realistic time estimate for completion, e.g., "8 hours", "12 hours")
- suggestions: (practical tips for instructors and students, including recommended activities, challenges, resources, or teaching strategies)

IMPORTANT GUIDELINES:
- Ensure modules build upon previous knowledge
- Balance theoretical concepts with practical application
- Consider different learning styles and engagement strategies
- Provide clear learning progression throughout the course
- Make descriptions specific and actionable

Strictly return the output as a JSON object matching this schema:
{{
  "course_id": "{outline.get('course_id', 'N/A')}",
  "modules": [
    {{
      "module_title": "...",
      "description": "...",
      "module_hours": "...",
      "suggestions": "..."
    }},
    ...
  ]
}}
"""
    response = llmclient.models.generate_content(
        model="gemini-2.5-flash",
        contents="",
        config=GenerateContentConfig(
            system_instruction=prompt,
            response_mime_type="application/json"
        )
    )
    # Parse the response as a structured object
    import json
    result = json.loads(response.text)
    return result.get('modules', [])

def redo_modules_from_outline(outline: Dict[str, Any], prev_modules: List[Dict], user_suggestion: str, num_modules: int = 5) -> List[Dict]:
    system_prompt = f"""
You are a course module design assistant. You are given a previously generated list of modules for a course.
The user has provided a suggestion to modify or improve these modules.

Use the suggestion to regenerate the modules appropriately. You may revise module titles, descriptions, hours, or suggestions, but maintain the overall structure and alignment with the original course metadata.

### Course Outline:
{outline}

### Previous Modules:
{prev_modules}

### Requirements:
- Create exactly {num_modules} modules
- Ensure logical progression from basic to advanced concepts
- Distribute content evenly across modules
- Align with the course's learning outcomes and objectives
- Consider the target audience and prerequisites

### Instructions:
- Do NOT discard useful content from previous modules unless the suggestion implies it.
- Refine and regenerate the modules with improvements based on the user suggestion.
- Maintain the expected format and ensure clarity and student focus.
- Ensure modules build upon previous knowledge
- Balance theoretical concepts with practical application

### Output Format:
Strictly return the revised modules as a JSON object matching this schema:
{{
  "course_id": "{outline.get('course_id', 'N/A')}",
  "modules": [
    {{
      "module_title": "...",
      "description": "...",
      "module_hours": "...",
      "suggestions": "..."
    }},
    ...
  ]
}}
"""
    
    user_content = Content(role="user", parts=[Part(text=user_suggestion)])
    response = llmclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_content,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json"
        )
    )
    
    # Parse the response as a structured object
    import json
    result = json.loads(response.text)
    return result.get('modules', [])

def main(outline: Dict[str, Any]):
    modules = generate_modules_from_outline(outline, num_modules=5)
    print("Generated Modules:\n")
    for idx, module in enumerate(modules):
        print(f"Module {idx+1}: {module['module_title']}")
        print(f"Description: {module['description']}")
        print(f"Hours: {module['module_hours']}")
        # Get suggestions for this module
        suggestion_json = get_stage_suggestions(
            stage="module",
            context=module['description'],
            feedback_mode="light"
        )
        print(f"Suggestions: {suggestion_json}\n{'-'*40}")
    
    return modules


if __name__ == "__main__":
    # This will only run if the file is executed directly
    # You should call main(outline) from another file with the actual outline
    print("This module should be imported and called with an outline parameter.")
    print("Example usage: main(your_outline_dict)")
