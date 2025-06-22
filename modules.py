from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import re
import os
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
load_dotenv()

# Import the suggestion logic from external file
from suggestion_logic import get_stage_suggestions

app = FastAPI(title="Module Generator API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY"),
    "model": "gemini-1.5-flash-latest",
    "base_url": "https://generativelanguage.googleapis.com/v1beta"
}

class ModuleGenerationRequest(BaseModel):
    outline: Dict[str, Any]
    includeSuggestions: Optional[bool] = True

class ModuleRebuildRequest(BaseModel):
    currentModules: List[dict]
    changeDescription: str
    outline: Dict[str, Any]
    includeSuggestions: Optional[bool] = True

class ModuleGenerationResponse(BaseModel):
    success: bool
    message: str
    modules: List[dict]

def extract_hours_from_duration(duration: str, credits: int = 0) -> int:
    if not duration and not credits:
        return 40
    
    if duration:
        hours_match = re.search(r'(\d+)\s*hours?', duration.lower())
        if hours_match:
            return int(hours_match.group(1))
        weeks_match = re.search(r'(\d+)\s*weeks?', duration.lower())
        if weeks_match:
            return int(weeks_match.group(1)) * 3
        months_match = re.search(r'(\d+)\s*months?', duration.lower())
        if months_match:
            return int(months_match.group(1)) * 12
    
    return credits * 15 if credits else 40

def create_generation_prompt(course_data: Dict[str, Any]) -> str:
    return f"""
You are an expert curriculum designer. Generate a comprehensive list of modules for the following course:

**Course Title:** {course_data.get('courseTitle', '')}
**Course Description:** {course_data.get('courseDescription', '')}
**Total Hours:** {course_data.get('totalHours', 40)}
**Duration:** {course_data.get('duration', '')}
**Credits:** {course_data.get('credits', 0)}

**Learning Outcomes:**
{chr(10).join(f"- {outcome}" for outcome in course_data.get('learningOutcomes', []))}

**Prerequisites:**
{chr(10).join(f"- {prereq}" for prereq in course_data.get('prerequisites', []))}

Generate 4-8 modules that:
1. Cover all learning outcomes comprehensively
2. Are logically sequenced from basic to advanced concepts
3. Have realistic hour allocations that sum to approximately {course_data.get('totalHours', 40)} hours
4. Include practical application and assessment opportunities
5. Build upon prerequisites and each other

For each module, provide:
- name: Clear, descriptive title
- description: Detailed description (2-3 sentences) of what students will learn
- duration: Realistic time allocation in hours

Return ONLY a valid JSON array of modules, no additional text or formatting.

Example format:
[
  {{
    "name": "Introduction to Course Topic",
    "description": "Students will learn fundamental concepts...",
    "duration": 8
  }}
]
"""

def create_rebuild_prompt(course_data: Dict[str, Any]) -> str:
    current_modules_text = "\n".join([
        f"{i+1}. {mod.get('name', '')} ({mod.get('duration', 0)} hours): {mod.get('description', '')}"
        for i, mod in enumerate(course_data.get('currentModules', []))
    ])
    
    return f"""
You are an expert curriculum designer. Rebuild the module structure for this course based on the requested changes:

**Course Title:** {course_data.get('courseTitle', '')}
**Course Description:** {course_data.get('courseDescription', '')}
**Total Hours:** {course_data.get('totalHours', 40)}

**Current Modules:**
{current_modules_text}

**Requested Changes:** {course_data.get('changeDescription', '')}

**Learning Outcomes:**
{chr(10).join(f"- {outcome}" for outcome in course_data.get('learningOutcomes', []))}

Rebuild the modules to:
1. Address the requested changes effectively
2. Maintain logical progression and coherence
3. Keep total hours around {course_data.get('totalHours', 40)}
4. Preserve valuable content from existing modules where appropriate
5. Ensure all learning outcomes are still covered

Return ONLY a valid JSON array of the rebuilt modules.

Example format:
[
  {{
    "name": "Updated Module Title",
    "description": "Enhanced description addressing the changes...",
    "duration": 8
  }}
]
"""

async def call_gemini_api(prompt: str) -> str:
    if not GEMINI_CONFIG["api_key"]:
        raise ValueError("GEMINI_API_KEY not found")
    
    url = f"{GEMINI_CONFIG['base_url']}/models/{GEMINI_CONFIG['model']}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_CONFIG["api_key"]}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {response.text}")
        
        result = response.json()
        if "candidates" not in result or not result["candidates"]:
            raise ValueError("No response from Gemini API")
        
        return result["candidates"][0]["content"]["parts"][0]["text"]

def generate_module_suggestions(module: Dict[str, Any], course_context: Dict[str, Any]) -> List[str]:
    """Generate AI suggestions for a specific module using external suggestion logic"""
    try:
        # Prepare context for the suggestion system
        module_context = f"""
Course Title: {course_context.get('courseTitle', '')}
Course Description: {course_context.get('courseDescription', '')}
Total Course Hours: {course_context.get('totalHours', 40)}

Module Details:
- Name: {module.get('name', '')}
- Description: {module.get('description', '')}
- Duration: {module.get('duration', 0)} hours

Learning Outcomes to Address:
{chr(10).join(f"- {outcome}" for outcome in course_context.get('learningOutcomes', []))}
"""
        
        # Use the external suggestion logic directly
        response = get_stage_suggestions(
            stage="module",
            context=module_context,
            feedback_mode="light"
        )
        
        # Parse the response if it's a string (JSON)
        if isinstance(response, str):
            # Remove markdown code blocks if present
            cleaned_response = response.strip()
            
            # Handle multiple variations of code block markers
            if '```json' in cleaned_response:
                start_marker = cleaned_response.find('```json') + 7
                end_marker = cleaned_response.rfind('```')
                if end_marker > start_marker:
                    cleaned_response = cleaned_response[start_marker:end_marker].strip()
            elif cleaned_response.startswith('```') and cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[3:-3].strip()
            elif '```' in cleaned_response:
                lines = cleaned_response.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('```'):
                        in_json = not in_json
                        continue
                    if in_json or (line.strip().startswith('{') or line.strip().startswith('[')):
                        json_lines.append(line)
                cleaned_response = '\n'.join(json_lines).strip()
            
            # Try to find JSON content even if parsing fails
            if not cleaned_response.startswith(('{', '[')):
                json_start = max(cleaned_response.find('{'), cleaned_response.find('['))
                if json_start != -1:
                    json_end = max(cleaned_response.rfind('}'), cleaned_response.rfind(']'))
                    if json_end > json_start:
                        cleaned_response = cleaned_response[json_start:json_end+1]
            
            try:
                parsed_response = json.loads(cleaned_response)
                
                if isinstance(parsed_response, dict) and "suggestions" in parsed_response:
                    suggestions = parsed_response["suggestions"]
                    if isinstance(suggestions, list):
                        return suggestions
                elif isinstance(parsed_response, list):
                    return parsed_response
                    
            except json.JSONDecodeError:
                # Last resort: try to extract suggestions using regex
                try:
                    suggestions_match = re.search(r'"suggestions"\s*:\s*\[(.*?)\]', cleaned_response, re.DOTALL)
                    if suggestions_match:
                        suggestions_str = '[' + suggestions_match.group(1) + ']'
                        suggestions = json.loads(suggestions_str)
                        return suggestions
                except Exception:
                    pass
        
        # If response is already a dict
        elif isinstance(response, dict):
            if "suggestions" in response:
                suggestions = response["suggestions"]
                if isinstance(suggestions, list):
                    return suggestions
        
        return []
        
    except Exception as e:
        print(f"Error generating suggestions for module '{module.get('name', 'Unknown')}': {str(e)}")
        return []

def parse_modules_response(response_text: str) -> List[Dict[str, Any]]:
    response_text = response_text.strip()
    
    # Remove markdown code blocks
    response_text = re.sub(r'```(?:json)?\s*', '', response_text)
    response_text = re.sub(r'```\s*$', '', response_text)
    
    # Extract JSON array
    json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
    json_text = json_match.group(0) if json_match else response_text
    
    try:
        modules = json.loads(json_text)
        if not isinstance(modules, list):
            raise ValueError("Response is not a list of modules")
        
        validated_modules = []
        for i, module in enumerate(modules):
            if isinstance(module, dict):
                validated_modules.append({
                    "name": str(module.get("name", f"Module {i+1}")).strip(),
                    "description": str(module.get("description", "")).strip(),
                    "duration": max(1, int(module.get("duration", 5)))
                })
        
        return validated_modules
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in response: {str(e)}")

@app.get("/")
async def root():
    return {"message": "FastAPI Module Generator is running!", "endpoints": ["/docs", "/health", "/api/modules/generate", "/api/modules/rebuild"]}

@app.post("/api/modules/generate", response_model=ModuleGenerationResponse)
async def generate_modules(request: ModuleGenerationRequest):
    try:
        outline = request.outline
        if not outline or not outline.get("title") or not outline.get("description"):
            raise HTTPException(status_code=400, detail="Outline must contain title and description")

        course_data = {
            "courseTitle": outline.get("title", ""),
            "courseDescription": outline.get("description", ""),
            "learningOutcomes": outline.get("learning_outcomes", []),
            "prerequisites": outline.get("prerequisites", []),
            "totalHours": extract_hours_from_duration(outline.get("duration", ""), outline.get("credits", 0)),
            "duration": outline.get("duration", ""),
            "credits": outline.get("credits", 0)
        }

        print(f"Generating modules for: {course_data['courseTitle']}")
        
        prompt = create_generation_prompt(course_data)
        response = await call_gemini_api(prompt)
        modules = parse_modules_response(response)

        # Generate suggestions for each module if requested using external logic
        if request.includeSuggestions:
            print("Generating AI suggestions for modules...")
            for i, module in enumerate(modules, 1):
                print(f"Processing module {i}/{len(modules)}: {module['name']}")
                suggestions = generate_module_suggestions(module, course_data)
                module["suggestions"] = suggestions

        print("\n" + "="*50)
        print("GENERATED MODULES:")
        print("="*50)
        
        # Print clean, formatted output
        for i, module in enumerate(modules, 1):
            print(f"\n{i}. {module['name']} ({module['duration']} hours)")
            print(f"   {module['description']}")
            if module.get('suggestions'):
                print(f"   Suggestions: {len(module['suggestions'])} items")

        print("\n" + "="*50)
        print("JSON OUTPUT:")
        print("="*50)
        print(json.dumps(modules, indent=2, ensure_ascii=False))

        return ModuleGenerationResponse(
            success=True,
            message="Modules generated successfully from course outline with AI suggestions.",
            modules=modules
        )

    except Exception as error:
        print(f"Error: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@app.post("/api/modules/rebuild", response_model=ModuleGenerationResponse)
async def rebuild_modules(request: ModuleRebuildRequest):
    try:
        if not all([request.changeDescription, request.outline, request.currentModules]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        outline = request.outline
        course_data = {
            "courseTitle": outline.get("title", ""),
            "courseDescription": outline.get("description", ""),
            "learningOutcomes": outline.get("learning_outcomes", []),
            "prerequisites": outline.get("prerequisites", []),
            "totalHours": extract_hours_from_duration(outline.get("duration", ""), outline.get("credits", 0)),
            "currentModules": request.currentModules,
            "changeDescription": request.changeDescription
        }

        print(f"Rebuilding modules for: {course_data['courseTitle']}")
        print(f"Change requested: {request.changeDescription}")

        prompt = create_rebuild_prompt(course_data)
        response = await call_gemini_api(prompt)
        new_modules = parse_modules_response(response)

        # Generate suggestions for each rebuilt module if requested using external logic
        if request.includeSuggestions:
            print("Generating AI suggestions for rebuilt modules...")
            for i, module in enumerate(new_modules, 1):
                print(f"Processing module {i}/{len(new_modules)}: {module['name']}")
                suggestions = generate_module_suggestions(module, course_data)
                module["suggestions"] = suggestions

        print("\n" + "="*50)
        print("REBUILT MODULES:")
        print("="*50)
        
        # Print clean, formatted output
        for i, module in enumerate(new_modules, 1):
            print(f"\n{i}. {module['name']} ({module['duration']} hours)")
            print(f"   {module['description']}")
            if module.get('suggestions'):
                print(f"   Suggestions: {len(module['suggestions'])} items")

        print("\n" + "="*50)
        print("JSON OUTPUT:")
        print("="*50)
        print(json.dumps(new_modules, indent=2, ensure_ascii=False))

        return ModuleGenerationResponse(
            success=True,
            message="Modules successfully rebuilt based on your requirements with AI suggestions.",
            modules=new_modules
        )

    except Exception as error:
        print(f"Error during rebuild: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
