from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from genai_logic import generate_course_outline, redo_course_outline, CourseInit, CourseOutline
from suggestion_logic import get_stage_suggestions
import uuid
import json

router = APIRouter()
course_context = {}


@router.post("/init-course")
def init_course(course: CourseInit):
    course_id = course.course_id or str(uuid.uuid4())

    if course_id in course_context:
        raise HTTPException(status_code=400, detail="Course ID already exists")

    outline_text = generate_course_outline(course)

    try:
        outline_json = json.loads(outline_text) if outline_text else {"raw": ""}
    except json.JSONDecodeError:
        outline_json = {"raw": outline_text or ""}

    try:
        suggestions = get_stage_suggestions(stage="outline", context=outline_text)
        suggestions_json = json.loads(suggestions) if isinstance(suggestions, str) else suggestions
    except Exception as e:
        suggestions_json = {"raw": f"Suggestion generation failed: {str(e)}"}

    # Save in memory
    course_context[course_id] = {
        "metadata": course,
        "outline": outline_json,
        "modules": [],
        "suggestions": {
            "outline": suggestions_json
        }
    }

    return {
        "message": "Course initialized",
        "course_id": course_id,
        "outline": outline_json,
        "suggestions": suggestions_json
    }


class RedoRequest(BaseModel):
    course_id: str
    user_suggestion: str


@router.post("/redo-outline")
def redo_outline(request: RedoRequest):
    course_id = request.course_id

    if course_id not in course_context:
        raise HTTPException(status_code=404, detail="Course ID not found")

    course_data = course_context[course_id]
    course_metadata = course_data["metadata"]
    prev_outline_dict = course_data["outline"]
    user_suggestion = request.user_suggestion

    try:
        # Convert dict to CourseOutline Pydantic model
        prev_outline = CourseOutline(**prev_outline_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse previous outline: {str(e)}")

    try:
        new_outline_text = redo_course_outline(course_metadata, prev_outline, user_suggestion)
        
        try:
            new_outline = json.loads(new_outline_text) if new_outline_text else {"raw": ""}
        except json.JSONDecodeError as e:
            print("⚠️ JSON decode error in LLM response:", e)
            print("🔍 Raw outline text:", new_outline_text)
            new_outline = {"raw": new_outline_text or ""}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outline regeneration failed: {str(e)}")

    try:
        suggestions = get_stage_suggestions(stage="outline", context=new_outline_text)
        suggestions_json = json.loads(suggestions) if isinstance(suggestions, str) else suggestions
    except Exception as e:
        suggestions_json = {"raw": f"Suggestion generation failed: {str(e)}"}

    # Update context
    course_context[course_id]["outline"] = new_outline
    course_context[course_id]["suggestions"]["outline"] = suggestions_json

    return {
        "message": "Course outline regenerated successfully",
        "course_id": course_id,
        "outline": new_outline,
        "suggestions": suggestions_json
    }
