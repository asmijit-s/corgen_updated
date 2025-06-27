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
from course_content_generator import (
    generate_reading_material,
    generate_lecture_script,
    generate_quiz,
    generate_assignment,
    generate_mindmap,
    ReadingInput,
    LectureInput,
    QuizInput,
    AssignmentInput,
    MindmapInput,
    QuizOut
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
    submodule_id :str
    submodule_name :str
    submodule_description: str
    activity_types: List[str]
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
def generate_activity(payload: ActivityRequest):
    logger.info("Generating activities...")
    submodule = Submodule(
        submodule_id=payload.submodule_id,
        submodule_title=payload.submodule_name,
        submodule_description=payload.submodule_description
    )
    result_str = generate_activities(
        submodule=submodule,
        activity_types=",".join(payload.activity_types),
        user_instructions=payload.user_instructions
    )
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)
    result = parse_result(result_str, ActivitySet)
    course_state[payload.submodule_id] = course_state.get(payload.submodule_id, {})
    course_state[payload.submodule_id]["activities"] = result
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

# course_content_generator.py (complete with endpoints)

# ... (imports, utilities, models, and content generators already defined above) ...

# ----------------------------- API Endpoints -----------------------------

@router.post("/generate-reading-material")
def api_generate_reading(input: ReadingInput):
    try:
        output, summaries = generate_reading_material(
            course_outline=input.course_outline,
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            user_prompt=input.user_prompt,
            previous_material_summary=input.previous_material_summary,
            notes_path=input.notes_path,
            pdf_path=input.pdf_path,
            url=input.url
        )
        return {
            "readingMaterial": output["readingMaterial"],
            "readingMaterialSummary": output["readingMaterialSummary"],
            "sourceSummaries": summaries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-lecture-script")
def api_lecture(input: LectureInput):
    try:
        script, summaries, script_summary = generate_lecture_script(
            course_outline=input.course_outline,
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            user_prompt=input.user_prompt,
            prev_activities_summary=input.prev_activities_summary,
            notes_path=input.notes_path,
            pdf_path=input.pdf_path,
            text_examples=input.text_examples,
            duration_minutes=input.duration_minutes
        )
        return {
            "lectureScript": script,
            "sourceSummaries": summaries,
            "lectureScriptSummary": script_summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-quiz", response_model=List[QuizOut])
def api_generate_quiz(input: QuizInput):
    try:
        quiz = generate_quiz(
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            material_summary=input.material_summary,
            number_of_questions=input.number_of_questions,
            quiz_type=input.quiz_type,
            total_score=input.total_score,
            user_prompt=input.user_prompt
        )
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-assignment")
def api_generate_assignment(input: AssignmentInput):
    try:
        assignment = generate_assignment(
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            user_prompt=input.user_prompt,
            all_submodule_summaries=input.all_submodule_summaries
        )
        return {"assignment": assignment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-mindmap")
def api_generate_mindmap(input: MindmapInput):
    try:
        mindmap = generate_mindmap(
            module_name=input.module_name,
            submodule_summaries=input.submodule_summaries
        )
        return {"mindmap": mindmap}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

