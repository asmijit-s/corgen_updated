# api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from genai_logic import generate_course_outline, CourseInit
import uuid
import json

course_context = {}

router = APIRouter()


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
