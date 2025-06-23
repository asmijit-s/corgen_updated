from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from genai_logic import (
    CourseInit, CourseOutline, Module, ModuleSet, SubmoduleSet,
    generate_course_outline, redo_course_outline,
    generate_modules, redo_modules,
    generate_submodules, redo_submodules,
    generate_activities, redo_activities,
    Stage, get_stage_suggestions
)

router = APIRouter()

# --------------------------- COURSE OUTLINE ---------------------------

@router.post("/generate/outline")
def api_generate_course_outline(course: CourseInit):
    result = generate_course_outline(course)
    return {"result": result}

@router.post("/redo/outline")
def api_redo_course_outline(
    course: CourseInit,
    prev_outline: CourseOutline,
    suggestion: str = Body(...)
):
    result = redo_course_outline(course, prev_outline, suggestion)
    return {"result": result}

# --------------------------- MODULES ---------------------------

@router.post("/generate/modules")
def api_generate_modules(course_outline: CourseOutline):
    result = generate_modules(course_outline)
    return {"result": result}

@router.post("/redo/modules")       
def api_redo_modules(
    course_outline: CourseOutline,
    prev_modules: ModuleSet,
    suggestion: str = Body(...)
):
    result = redo_modules(course_outline, prev_modules, suggestion)
    return {"result": result}

# --------------------------- SUBMODULES ---------------------------

@router.post("/generate/submodules")
def api_generate_submodules(module: dict):
    result = generate_submodules(Module(**module))
    return {"result": result}

@router.post("/redo/submodules")
def api_redo_submodules(
    module: dict,
    prev_submodules: dict,
    suggestion: str = Body(...)
):
    result = redo_submodules(Module(**module), SubmoduleSet(**prev_submodules), suggestion)
    return {"result": result}

# --------------------------- ACTIVITIES ---------------------------

class ActivityRequest(BaseModel):
    submodule_name: str
    submodule_description: str
    activity_types: str
    user_instructions: Optional[str] = None

@router.post("/generate/activities")
def api_generate_activities(req: ActivityRequest):
    result = generate_activities(
        submodule_name=req.submodule_name,
        submodule_description=req.submodule_description,
        activity_types=req.activity_types,
        user_instructions=req.user_instructions
    )
    return {"result": result}

class RedoActivityRequest(BaseModel):
    existing_activities: List[dict]
    submodule_name: str
    submodule_description: str
    suggestion: str

@router.post("/redo/activities")
def api_redo_activities(req: RedoActivityRequest):
    result = redo_activities(
        existing_activities=req.existing_activities,
        submodule_name=req.submodule_name,
        submodule_description=req.submodule_description,
        user_suggestion=req.suggestion
    )
    return {"result": result}

# --------------------------- STAGE SUGGESTIONS ---------------------------

class StageSuggestionRequest(BaseModel):
    stage: Stage
    context: str
    feedback_mode: Optional[str] = "light"

@router.post("/suggestions/stage")
def api_stage_suggestions(req: StageSuggestionRequest):
    suggestions = get_stage_suggestions(
        stage=req.stage,
        context=req.context,
        feedback_mode=req.feedback_mode if req.feedback_mode is not None else "light"
    )
    return {"suggestions": suggestions}
