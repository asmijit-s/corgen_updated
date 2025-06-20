# api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from genai_logic import generate_course_outline, CourseInit
import uuid
import json
from activity_gen import (
    generate_activities,
    rebuild_activity_list,
    Activity
)

course_context = {}

router = APIRouter()

class GenerateRequest(BaseModel):
    submodule_name: str
    submodule_description: str
    activity_types: List[str]
    user_instructions: str = None

class RebuildRequest(BaseModel):
    existing_activities: List[Activity]
    submodule_name: str
    submodule_description: str
    user_suggestion: str

@router.post("/generate-activities")
def generate_activities_api(request: GenerateRequest):
    try:
        activities = generate_activities(
            submodule_name=request.submodule_name,
            submodule_description=request.submodule_description,
            activity_types=request.activity_types,
            user_instructions=request.user_instructions
        )
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rebuild-activities")
def rebuild_activities_api(request: RebuildRequest):
    try:
        activities = rebuild_activity_list(
            existing_activities=[act.dict() for act in request.existing_activities],
            submodule_name=request.submodule_name,
            submodule_description=request.submodule_description,
            user_suggestion=request.user_suggestion
        )
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/init-course")
def init_course(course: CourseInit):
    course_id = course.course_id or str(uuid.uuid4())

    if course_id in course_context:
        raise HTTPException(status_code=400, detail="Course ID already exists")

    outline_text = generate_course_outline(course)

    try:
        if outline_text is not None:
            outline_json = json.loads(outline_text)
        else:
            outline_json = {"raw": ""}
    except json.JSONDecodeError:
        outline_json = {"raw": outline_text if outline_text is not None else ""}

    course_context[course_id] = {
        "metadata": course,
        "outline": outline_json,
        "modules": []  # Will be populated in next step
    }
    print("The generated course outline is as follows: ",'\n', outline_json)
    return {"message": "Course initialized", "course_id": course_id, "outline": outline_json}
