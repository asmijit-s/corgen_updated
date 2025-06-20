# suggestion_logic.py

from google import genai
from google.genai.types import GenerateContentConfig
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict, Optional

load_dotenv()

llmclient = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class SuggestionOutput(BaseModel):
    suggestions: List[str]
    message: str

def get_stage_suggestions(stage: str, context: str, feedback_mode: str = "light"):
    """
    Get AI-generated suggestions based on the current stage of course creation.

    Parameters:
    - stage: one of ["outline", "module", "submodule", "activity"]
    - context: the content generated/edited so far
    - feedback_mode: ["none", "light", "detailed"]
    """
    if feedback_mode == "none":
        return SuggestionOutput(suggestions=[], message="Feedback mode disabled.").model_dump()

    prompt = f"""
You are a course design assistant reviewing a course at the '{stage}' stage.
Based on the current content provided below, offer {"concise" if feedback_mode == "light" else "detailed"} suggestions 
for improvements, additions, or structural changes the SME might consider.

Current Context:
{context}
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
