from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict

from genai_logic import (
    CourseInit,
    CourseOutline,
    ModuleSet,
    Module,
    SubmoduleSet,
    Submodule,
    ActivitySet,
    generate_course_outline,
    redo_course_outline,
    generate_modules,
    redo_modules,
    generate_submodules,
    redo_submodules,
    generate_activities,
    redo_activities,
    get_stage_suggestions,
    Stage
)
import json
import logging
from typing import Optional

router = APIRouter()

# Configure logging
logger = logging.getLogger("course_api")
logging.basicConfig(level=logging.INFO)

# In-memory course state for tracking previous stages
course_state = {}

class RedoRequest(BaseModel):
    course_id: str
    user_message: str

class ActivityRequest(BaseModel):
    submodule_id: str
    submodule_description: str
    activity_types: List[str]
    user_instructions: Optional[str] = None

def as_json(obj: BaseModel | dict) -> str:
    return json.dumps(obj.model_dump() if isinstance(obj, BaseModel) else obj, indent=2)

def parse_result(result_str: str | None, model: type[BaseModel]) -> BaseModel:
    if not result_str:
        logger.error("LLM returned no result.")
        raise HTTPException(status_code=500, detail="No result returned from LLM")
    try:
        raw_data = json.loads(result_str)
        validated = model.model_validate(raw_data)
        return validated
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse LLM result as JSON.")
        raise HTTPException(status_code=500, detail="Invalid result format from LLM")
    except ValidationError as ve:
        logger.exception("Parsed result failed schema validation.")
        raise HTTPException(status_code=500, detail=f"Schema validation failed: {ve.errors()}")

@router.post("/generate/outline")
def generate_outline(course: CourseInit):
    logger.info("Generating course outline...")
    result_str = generate_course_outline(course)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, CourseOutline)
    course_state[course.course_id] = {
        "course_init": course.model_dump(),
        "outline": result
    }
    suggestions = get_stage_suggestions(Stage.outline, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/redo/outline")
def redo_outline(payload: RedoRequest):
    logger.info("Redoing outline...")
    state = course_state.get(payload.course_id)
    if not state or "outline" not in state or "course_init" not in state:
        raise HTTPException(status_code=400, detail="No previous outline or course found for this course ID")
    course_init_obj = CourseInit(**state["course_init"])
    outline_obj = state["outline"]
    result_str = redo_course_outline(course_init_obj, outline_obj, payload.user_message)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, CourseOutline)
    course_state[payload.course_id]["outline"] = result
    suggestions = get_stage_suggestions(Stage.outline, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/generate/modules")
def generate_module(course_outline: CourseOutline):
    logger.info("Generating modules...")
    result_str = generate_modules(course_outline)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, ModuleSet)
    course_entry = course_state.setdefault(course_outline.course_id, {})
    course_entry["modules"] = result    
    suggestions = get_stage_suggestions(Stage.module, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/redo/modules")
def redo_module(payload: RedoRequest):
    logger.info("Redoing modules...")
    state = course_state.get(payload.course_id)
    if not state or "modules" not in state or "outline" not in state:
        raise HTTPException(status_code=400, detail="No previous modules or outline found for this course ID")
    outline_obj = CourseOutline(**state["outline"])
    modules_obj = ModuleSet(**state["modules"])
    result_str = redo_modules(outline_obj, modules_obj, payload.user_message)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, ModuleSet)
    course_state[payload.course_id]["modules"] = result
    suggestions = get_stage_suggestions(Stage.module, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/generate/submodules")
def generate_submodule(module: Module):
    logger.info("Generating submodules...")
    result_str = generate_submodules(module)
    if not result_str:
        raise HTTPException(status_code=400, detail="Failed to generate submodules")

    # No need to parse again if `call_llm` already validated:
    result = result_str
    course_state[module.module_id] = course_state.get(module.module_id, {})
    course_state[module.module_id]["submodules"] = result
    suggestions = get_stage_suggestions(Stage.submodule, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/redo/submodules")
def redo_submodule(payload: RedoRequest):
    logger.info("Redoing submodules...")
    state = course_state.get(payload.course_id)
    if not state or "submodules" not in state or "modules" not in state:
        raise HTTPException(status_code=400, detail="No previous submodules or module found for this ID")
    module_obj = Module(**state["modules"]["modules"][0]) if state["modules"].get("modules") else None
    if not module_obj:
        raise HTTPException(status_code=400, detail="Module information incomplete.")
    submodule_set_obj = SubmoduleSet(**state["submodules"])
    result_str = redo_submodules(module_obj, submodule_set_obj, payload.user_message)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, SubmoduleSet)
    course_state[payload.course_id]["submodules"] = result
    suggestions = get_stage_suggestions(Stage.submodule, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/generate/activities")
def generate_activity(payload: ActivityRequest):
    print("maa chud gyi")
    logger.info("Generating activities...")
    result = generate_activities(
        payload.submodule_id,
        payload.submodule_description,
        payload.activity_types,
        payload.user_instructions
    )

    if not result:
        raise HTTPException(status_code=400, detail="Failed to generate activities")

    course_state[payload.submodule_id] = course_state.get(payload.submodule_id, {})
    course_state[payload.submodule_id]["activities"] = result

    suggestions = get_stage_suggestions(Stage.activity, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/redo/activities")
def redo_activity(payload: RedoRequest):
    logger.info("Redoing activities...")
    state = course_state.get(payload.course_id)
    if not state or "activities" not in state or "submodules" not in state:
        raise HTTPException(status_code=400, detail="No previous activities or submodule context found for this ID")
    submodule_data = state["submodules"]["submodules"][0] if state["submodules"].get("submodules") else None
    if not submodule_data:
        raise HTTPException(status_code=400, detail="Submodule information incomplete.")
    activities = state["activities"]["activities"]
    result_str = redo_activities(
        activities,
        submodule_data["submodule_title"],
        submodule_data["submodule_description"],
        payload.user_message
    )
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, ActivitySet)
    course_state[payload.course_id]["activities"] = result
    suggestions = get_stage_suggestions(Stage.activity, as_json(result))
    return {"result": result, "suggestions": suggestions}