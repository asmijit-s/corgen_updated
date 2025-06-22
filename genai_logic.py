# genai_logic.py

import os
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Content, Part
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Optional

load_dotenv()

llmclient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))   


class CourseInit(BaseModel):
    course_id: str
    title: str
    prerequisites: List[str]
    description: str
    learning_objectives: List[str]
    target_audience: str
    duration: str
    credits: int

class CourseOutline(BaseModel):
    course_id: str
    title: str
    prerequisites: List[str]
    description: str
    learning_outcomes: List[str]
    duration: str
    credits: int


def generate_course_outline(course: CourseInit) -> str:
    #- Learning Objectives: {', '.join(course.learning_objectives)} removed this for now 
    prompt = f"""
You are an expert course design assistant. Based on the following inputs, generate a detailed course outline:

INPUTS:
- Title: {course.title}
- Prerequisites: {course.prerequisites}
- Description: {course.description}
- Learning Objective: {', '.join(course.learning_objectives)}
- Target Audience: {course.target_audience}
- Duration: {course.duration}
- Credits: {course.credits}

Strictly return the output in the following format with clearly labeled sections:
- Course ID:
- Title:
- Prerequisites:
- Description (Elaborate based on input):
- Learning OUTCOMES (Address skills gained by students, refer to instruction 1. Eg. 'Students will be able to...'):
- Total Duration:
- Total Credits

DEFINITIONS (NOT TO BE INCLUDED IN OUTPUT):
1) Title: Course title.
2) Description: It will contain information on what the course content will be, the broad topics and the focus. It will talk about the prerequisites to be fulfilled prior to enrolling in this course.
3) Learning Objectives: What the instructor intends to teach in the course.
4) Learning Outcomes: What the student will learn after completion of the course, i.e the skills obtained.
5) Target Audience: Demography of the target student.
6) Duration: Time duration (eg. 12 weeks)
7) Credits: Total course credits.

INSTRUCTIONS FOR GENERATION:
1) Translate the instructor-defined learning objectives into measurable, student-centered learning outcomes that reflect what the learner will be able to do by the end of the course.
2) Do not give breakdowns of credit or duration. Simply output the information given as input.
3) Ensure the description aligns with the learning objectives and outcomes. Avoid adding content not implied or supported by the inputs.
4) The learning outcomes and description should be appropriate and relevant to the target audience.
5) Strictly adhere to the output list format specified. The output should contain learning_outcomes NOT learning_objectives.
"""
    response = llmclient.models.generate_content(
        model="gemini-2.5-flash",
        contents="",
        config=GenerateContentConfig(
            system_instruction=prompt,
            response_mime_type="application/json",
            response_schema=CourseOutline
        )
    )
    return response.text or ""  

from google.genai.types import Content, Part, GenerateContentConfig

def redo_course_outline(course: CourseInit, prev_outline: CourseOutline, user_suggestion: str) -> str:
    """
    Regenerate the course outline based on user feedback/suggestions.
    """

    # Prepare the system-level instruction with full context
    system_prompt = f"""
You are a course design assistant. You are given a previously generated course outline.
Now, the user has provided a suggestion to modify or improve this outline.

Use this suggestion to regenerate the course outline appropriately. You may revise the learning outcomes,
enhance the description, clarify prerequisites, or make any other changes as needed — but ensure the overall
structure remains aligned with the original course metadata.

### Course Metadata:
- Title: {course.title}
- Prerequisites: {course.prerequisites}
- Description: {course.description}
- Learning Objectives: {', '.join(course.learning_objectives)}
- Target Audience: {course.target_audience}
- Duration: {course.duration}
- Credits: {course.credits}

### Previous Outline:
{prev_outline.model_dump_json(indent=2)}

### Instructions:
- Do NOT discard useful content from the previous outline unless the suggestion implies it.
- Refine and regenerate the outline with improvements.
- Maintain the expected format and ensure clarity and student focus.

### Output Format:
Strictly return the revised outline as a JSON object matching this schema:
- course_id
- title
- prerequisites
- description
- learning_outcomes
- duration
- credits
"""

    # Construct the user message (the suggestion)
    user_content = Content(role="user", parts=[Part(text=user_suggestion)])

    # Call the Gemini model
    response = llmclient.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_content,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=CourseOutline
        )
    )
    print("LLM Response:", response.text)  # Debugging line to see the response
    return response.text or ""
