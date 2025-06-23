import os
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig, Content, Part
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Optional, Type
import json

load_dotenv()

llmclient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY")) 

################## COMMON LLM CALL #######################################################
def call_llm(prompt: Content, system_prompt: str, response_schema: Type[BaseModel], debug: bool = False) -> Optional[dict]:
    try:
        response = llmclient.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        if debug:
            print("LLM Raw Response: ", response.text)
        parsed_response = None
        if response.text is not None:
            parsed_response = json.loads(response.text)
        return parsed_response
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None


################################# OUTLINE GENERATION ######################################################
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
    suggestions: Optional[str] = None


def generate_course_outline(course: CourseInit) -> str:
    #- Learning Objectives: {', '.join(course.learning_objectives)} removed this for now 
    prompt = f"""
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses. Based on the following inputs, generate a detailed course outline:

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
    user_content = Content(
        role="user",
        parts=[
            Part(text="Generate a course outline."),
        ]
    )
    response = call_llm(prompt=user_content, system_prompt=prompt, response_schema=CourseOutline)
    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."


def redo_course_outline(course: CourseInit, prev_outline: CourseOutline, user_suggestion: str) -> str:
    """
    Regenerate the course outline based on user feedback/suggestions.
    """
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
    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=CourseOutline
    )
    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."

############################### MODULE  GENERATION ######################################################
class Module(BaseModel):
    module_id: str
    module_title: str
    module_description: str
    module_hours: str

class ModuleSet(BaseModel):
    course_id: str
    modules: List[Module]
    suggestions: Optional[str] = None

def generate_modules(course_outline: CourseOutline) -> str:
    system_prompt = """
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses.Based on the given course outline, generate a logical set of course modules that progressively build on each other.

### TASK:
- Decide how many modules are appropriate based on the course's duration, target audience, learning outcomes, and depth described.
- Ensure logical progression from introductory to advanced concepts.
- Balance content evenly across modules.
- Consider audience level and prerequisites.

### Each module should include:
- module_id: a unique identifier (e.g., "module_1", "module_2")
- module_title: a clear, focused name
- module_description: detailed overview of content, learning goals, and practical skills
- module_hours: realistic duration (e.g., "6 hours", "10 hours")
- suggestions: optional teaching tips, activity ideas, or student challenges

### Output Format:
Return a JSON object with:
- course_id
- modules: list of module objects (title, description, module_hours, suggestions)
"""

    user_content = Content(
        role="user",
        parts=[
            Part(text="Generate suitable course modules for this course."),
            Part(text=json.dumps(course_outline.model_dump(), indent=2))

        ]
    )

    response = call_llm(prompt=user_content, system_prompt=system_prompt, response_schema=ModuleSet)

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."


def redo_modules(course_outline: CourseOutline, prev_modules: ModuleSet, user_suggestion: str) -> str:
    system_prompt = """
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses. You are given a previously generated set of course modules and a course outline.
Now, the user has provided a suggestion to modify or improve these modules.

Use this suggestion to regenerate the modules appropriately. You may revise module titles, descriptions, durations, or suggestions as needed — but ensure the overall structure remains aligned with the original course outline.

### Instructions:
- Do NOT discard useful content from the previous modules unless the suggestion implies it.
- Refine and regenerate the modules with improvements.
- Maintain the expected format and ensure logical progression and student engagement.
- Adjust module count only if the suggestion or outline clarity calls for it.

### Output Format:
Strictly return the revised modules as a JSON object with:
- course_id
- modules: list of module objects (module_title, description, module_hours, suggestions)
"""

    user_content = Content(
        role="user",
        parts=[
            Part(text="Suggestion: " + user_suggestion),
            Part(text="Course Outline:\n" + json.dumps(course_outline.model_dump(), indent=2)),
            Part(text="Previous Modules:\n" + json.dumps(prev_modules.model_dump(), indent=2))
        ]
    )

    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=ModuleSet
    )

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."

################################# SUBMODULE GENERATION ######################################################
class Submodule(BaseModel):
    submodule_id: str
    submodule_title: str
    submodule_description: str

class SubmoduleSet(BaseModel):
    module_id: str
    submodules: List[Submodule]
    suggestions: Optional[str] = None

def generate_submodules(module: Module) -> str:
    system_prompt = """
    You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses. Based on the provided module details, generate a set of submodules that break down the module into smaller, focused learning units.
    ### TASK:
    - Create submodules that logically progress from basic to advanced concepts.
    - Ensure each submodule covers a specific aspect of the module's content.
    - Each submodule should have a clear title and detailed description of the content, learning goals, and practical skills.

    ### Submodule Details:
    - Submodule ID: A unique identifier for each submodule (e.g., "submodule_1", "submodule_2")
    - Submodule Title: A clear, focused title for each submodule
    - Submodule Description: A detailed overview of the content, learning goals, and practical skills for each submodule

    Each submodule should be:
    - A logically scoped unit of learning under the module.
    - Clearly named.
    - Accompanied by a short beginner-friendly description (2-3 lines).
    - Proportional in quantity and depth to the module hours (i.e., more hours = more submodules or deeper concepts).

    ### Output Format:
    Return a JSON object with:
    - module_id: the ID of the parent module
    - submodules: list of submodule objects (submodule_title, submodule_description)
    """
    user_content=Content(
            role="user",
            parts=[
                Part(text="Module Info:\n" + json.dumps(module.model_dump(), indent=2)),
            ]
        )
    
    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=SubmoduleSet
    )

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."

def redo_submodules(module: Module, prev_submodules: SubmoduleSet, user_suggestion: str) -> str:
    system_prompt = """
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses. You are given a previously generated set of submodules for a course module.
Now, the user has provided a suggestion to modify or improve these submodules.

### Instructions:
- Do NOT discard useful content from the previous submodules unless the suggestion implies it.
- Refine and regenerate the submodules with improvements.
- Maintain the expected format and ensure logical progression and student engagement.
- Adjust submodule count only if the suggestion or outline clarity calls for it.

### Output Format:
Strictly return the revised submodules as a JSON object with:
- module_id
- submodules: list of submodule objects (submodule_title, submodule_description)
"""

    user_content = Content(
        role="user",
        parts=[
            Part(text="Suggestion: " + user_suggestion),
            Part(text="Module info:\n" + json.dumps(module.model_dump(), indent=2)),
            Part(text="Previous Submodules:\n" + json.dumps(prev_submodules.model_dump(), indent=2))
        ]
    )

    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=SubmoduleSet
    )

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."
################################# ACTIVITY GENERATION ######################################################
class Activity(BaseModel):
    activity_name: str
    activity_description: str
    activity_objective: str
    activity_type: str

class ActivitySet(BaseModel):
    activities: List[Activity]
    suggestions: Optional[str] = None

def generate_activities(submodule_name: str, submodule_description: str, activity_types: str, user_instructions: Optional[str] = None) -> str:
    system_prompt = f"""
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses.

Your task is to generate a list of learning activities for a course submodule. The user will provide the submodule name, description, and optionally a set of instructions and preferred activity types (like Lecture, Quiz, Assessment, etc.).

### Input:
- Submodule Name: {submodule_name}
- Submodule Description: {submodule_description}
- Preferred Activity Types: {activity_types}
- User Instructions (optional): {user_instructions or "None provided"}

### If no user instructions are provided, follow these general guidelines:
- Make activities clear, beginner-friendly, and well-aligned with the submodule's goal.
- Cover a mix of conceptual understanding and applied thinking.
- Ensure activities are engaging and useful for learners.
- Avoid duplication across types.
- There can be multiple activities of single type so as to best align with submodule's goal.

### Output Format:
Return the result strictly as a **JSON array** of activity objects. Each object should include:
- "activity_name": Title of the activity
- "activity_description": A short paragraph describing what the activity is
- "activity_objective": A specific learning objective or outcome for the activity
- "activity_type": One of the types provided (Lecture, Quiz, Assessment, Reading Material, Lab)

Now, generate the activity list based on the inputs provided.
"""

    user_content = Content(
        role="user",
        parts=[
            Part(text="Generate activities based on the provided inputs.")
        ]
    )

    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=ActivitySet
    )

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."

def redo_activities(
    existing_activities: List[Dict],
    submodule_name: str,
    submodule_description: str,
    user_suggestion: str
) -> str:
    system_prompt = f"""
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses.

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
- "activity_name"
- "activity_description"
- "activity_objective"
- "activity_type"

Return only the updated JSON array. No extra explanation.
"""

    user_content = Content(
        role="user",
        parts=[
            Part(text="Modify the following activities:"),
            Part(text=json.dumps(existing_activities, indent=2)),
            Part(text="Suggestion: " + user_suggestion)
        ]
    )

    response = call_llm(
        prompt=user_content,
        system_prompt=system_prompt,
        response_schema=ActivitySet
    )

    return json.dumps(response, indent=2) if response is not None else "Nothing was generated. Please try again."

########################################## STAGE SUGGESTIONS ########################################################
class SuggestionOutput(BaseModel):
    suggestions: List[str]
    message: str
from enum import Enum

class Stage(str, Enum):
    outline = "outline"
    module = "module"
    submodule = "submodule"
    activity = "activity"

def get_stage_suggestions(stage: Stage, context: str, feedback_mode: str = "light"):
    prompt = f"""
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses.

The course development process follows these stages:
1. **Outline Generation**: Includes title, prerequisites, description, learning outcomes, duration, credits.
2. **Module Creation**: Divides the course into coherent, topic-wise modules.
3. **Submodule Creation**: Each module is broken down into smaller, focused submodules.
4. **Activity Design**: Learning activities (lectures, quizzes, reading material, assignments, labs) are added under each submodule.

You are currently reviewing the course at the **'{stage}'** stage.

Please analyze the context below and return {"concise" if feedback_mode == "light" else "detailed"} suggestions for improving, expanding, or refining the content at this stage. If any important element is missing or can be clarified further, mention that as well.

STAGE_INSTRUCTIONS:
- "outline": "Focus on improving clarity, completeness of prerequisites, alignment between objectives and outcomes, and coherence of description.",
- "module": "Ensure logical grouping of topics, coverage of all outcomes, and balanced workload.",
- "submodule": "Check for progression, granularity, and coverage of all module elements.",
- "activity": "Suggest diverse pedagogical techniques, align with Bloom's taxonomy, ensure student engagement."

Current Context:
{context}

Read the stage instructions carefully.
"""

    try:
        response = llmclient.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=GenerateContentConfig(
                system_instruction=prompt,
                response_mime_type='application/json',
                response_schema=SuggestionOutput
            )
        )
        return response.text or ""
    except Exception as e:
        return {"error": str(e)}




