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
    QuizOut,
    ReadingMaterialOut,
    LectureScriptOut
)
# from validator import (    
#     validate_content_with_keywords,
#     summarize_validation_report,
#     ValidationResult,
#     ValidationSummary,
#     ValidateContentInput,
#     ValidateContentOut
# )
import json
import logging
from typing import Optional, Dict, Any
from fastapi.responses import JSONResponse

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

class ValidateRequest(BaseModel):
    content: str
    activity_name: str
    content_type: str  

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

    # Step 2: Dump course input (with nested fields) for storage
    course_dict = course.model_dump(mode="python")

    # Optional: Flatten audience fields for filtering in MongoDB
    audience = course.target_audience
    course_dict.update({
        "audience_type": audience.audienceType,
        "audience_grade": audience.grade,
        "audience_english_level": audience.english_level,
        "audience_math_level": audience.maths_level,
        "audience_specialization": audience.specialization,
        "audience_country": audience.country
    })

    # Step 3: Generate the outline from the LLM
    result_data = generate_course_outline(course)

    if result_data is None or not isinstance(result_data, dict):
        return {"error": "Failed to generate outline. Please try again."}

    try:
        result_str = json.dumps(result_data)
        result = parse_result(result_str, CourseOutline)
    except Exception as e:
        logger.exception("Failed to parse LLM response into CourseOutline")
        return {"error": "LLM response could not be parsed."}

    # Step 6: Get suggestions for next stage
    suggestions = get_stage_suggestions(Stage.outline, as_json(result))

    # Final Response
    return {
        "result": result,
        "suggestions": suggestions
    }


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



@router.post("/generate-reading-material", response_model=ReadingMaterialOut)
def api_generate_reading(input: ReadingInput):
    try:
        result, _ = generate_reading_material(
            course_outline=input.course_outline,
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            activity_name=input.activity_name,
            activity_description=input.activity_description,
            activity_objective=input.activity_objective,
            user_prompt=input.user_prompt,
            previous_material_summary=input.previous_material_summary,
            notes_path=input.notes_path,
            pdf_path=input.pdf_path,
            url=input.url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-lecture-script", response_model=LectureScriptOut)
def api_lecture(input: LectureInput):
    try:
        # generate_lecture_script now returns a LectureScriptOut directly
        script, summaries, summary_text = generate_lecture_script(
            course_outline=input.course_outline,
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            activity_name=input.activity_name,
            activity_description=input.activity_description,
            activity_objective=input.activity_objective,
            user_prompt=input.user_prompt,
            prev_activities_summary=input.prev_activities_summary,
            notes_path=input.notes_path,
            pdf_path=input.pdf_path,
            text_examples=input.text_examples,
            duration_minutes=input.duration_minutes if input.duration_minutes is not None else 0
        )
        # If script is a dict, extract the main script text (assuming key 'lecture_script' or similar)
        script_text = script.get("lecture_script") if isinstance(script, dict) else script
        if script_text is None:
            script_text = ""
        return LectureScriptOut(
            lecture_script=script_text,
            source_summaries=summaries if isinstance(summaries, list) else None,
            lecture_script_summary=summary_text
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-quiz", response_model=List[QuizOut])
def api_generate_quiz(input: QuizInput):
    try:
        quiz_list = generate_quiz(
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            activity_name=input.activity_name,
            activity_description=input.activity_description,
            activity_objective=input.activity_objective,
            material_summary=input.material_summary,
            number_of_questions=input.number_of_questions,
            quiz_type=input.quiz_type,
            total_score=input.total_score,
            user_prompt=input.user_prompt
        )
        # If generate_quiz now returns a dict with a "quizzes" key, extract it
        if isinstance(quiz_list, dict) and "questions" in quiz_list:
            quiz_list = quiz_list["questions"]

        return quiz_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redo")
def redo_any_stage(request: RedoRequest):
    logger.info(f"Redoing stage: {request.stage}")
    found_prev = request.prev_content

    # Step 1: Get raw response string or dict from redo_stage
    result_str = redo_stage(request.stage, prev_content=found_prev, user_message=request.user_message)

    # Step 2: If already a dict, convert to JSON string
    if isinstance(result_str, dict):
        result_str = json.dumps(result_str)

    # Step 3: Map stage to appropriate schema
    schema_map = {
        Stage.outline: CourseOutline,
        Stage.module: ModuleSet,
        Stage.submodule: SubmoduleSet,
        Stage.activity: ActivitySet,
        Stage.reading: ReadingMaterialOut,
        Stage.lecture: LectureScriptOut,
        Stage.quiz: QuizOut,
    }

    schema = schema_map.get(request.stage)
    if schema is None:
        raise HTTPException(status_code=400, detail=f"Unsupported stage: {request.stage}")
    result = parse_result(result_str, schema)
    suggestions = get_stage_suggestions(request.stage, as_json(result))

    return {
        "result": result,
        "suggestions": suggestions
    }

# @router.post("/validate-content", response_model=ValidateContentOut)
# def api_validate_content(input: ValidateContentInput):
#     try:
#         detailed_report = validate_content_with_keywords(
#             content=input.content,
#             activity_name=input.activity_name,
#             activity_type=input.activity_type
#         )
#         validation_results = [
#             ValidationResult.model_validate(item) if not isinstance(item, ValidationResult) else item
#             for item in detailed_report
#         ]
#         summary = summarize_validation_report(validation_results)

#         return {
#             "summary": summary,
#             "detailedReport": detailed_report
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))