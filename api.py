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
    generate_modules,
    generate_submodules,
    generate_activities,
    get_stage_suggestions,
    redo_stage,
    Stage
)
import json
import logging
from typing import Optional, Dict, Any

router = APIRouter()

# Configure logging
logger = logging.getLogger("course_api")
logging.basicConfig(level=logging.INFO)

# In-memory course state for tracking previous stages
course_state = {}

class ActivityRequest(BaseModel):
<<<<<<< HEAD
    activity_types: str
=======
    submodule_id: str
    submodule_description: str
    activity_types: List[str]
>>>>>>> d81cd1ca7fc06401364933fdff4a6596c5806ac3
    user_instructions: Optional[str] = None

class RedoRequest(BaseModel):
    stage: Stage
    prev_content: Dict[str, Any]
    user_message: str

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

@router.post("/generate/activities")
<<<<<<< HEAD
def generate_activity(submodule: Submodule, payload: ActivityRequest):
    logger.info("Generating activities...")
    result_str = generate_activities(
        submodule,
        payload.activity_types,
        payload.user_instructions
    )
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, ActivitySet)
    course_state[submodule.submodule_id] = course_state.get(submodule.submodule_id, {})
    course_state[submodule.submodule_id]["activities"] = result
=======
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

>>>>>>> d81cd1ca7fc06401364933fdff4a6596c5806ac3
    suggestions = get_stage_suggestions(Stage.activity, as_json(result))
    return {"result": result, "suggestions": suggestions}

@router.post("/redo")
def redo_any_stage(request: RedoRequest):
    logger.info(f"Redoing stage: {request.stage}")
    found_prev= request.prev_content
    # Call the unified redo_stage function
    result_str = redo_stage(request.stage, prev_content=found_prev, user_message=request.user_message)
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result_str = parse_result(result_str, CourseOutline if request.stage == Stage.outline else ModuleSet if request.stage == Stage.module else SubmoduleSet if request.stage == Stage.submodule else ActivitySet)
    suggestions = get_stage_suggestions(request.stage, as_json(result_str))
    return {"result": result_str, "suggestions": suggestions}

