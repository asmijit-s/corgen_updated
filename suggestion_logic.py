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
    prompt = f"""
You are a course design assistant helping Subject Matter Experts (SMEs) design high-quality academic courses.

The course development process follows these stages:
1. **Outline Generation**: Includes title, prerequisites, description, learning outcomes, duration, credits.
2. **Module Creation**: Divides the course into coherent, topic-wise modules.
3. **Submodule Creation**: Each module is broken down into smaller, focused submodules.
4. **Activity Design**: Learning activities (lectures, quizzes, assignments, labs) are added under each submodule.

You are currently reviewing the course at the **'{stage}'** stage.

Please analyze the context below and return {"concise" if feedback_mode == "light" else "detailed"} suggestions for improving, expanding, or refining the content at this stage. If any important element is missing or can be clarified further, mention that as well.

STAGE_INSTRUCTIONS:
- "outline": "Focus on improving clarity, completeness of prerequisites, alignment between objectives and outcomes, and coherence of description.",
- "module": "Ensure logical grouping of topics, coverage of all outcomes, and balanced workload.",
- "submodule": "Check for progression, granularity, and coverage of all module elements.",
- "activity": "Suggest diverse pedagogical techniques, align with Bloom's taxonomy, ensure student engagement."

Current Context:
{context}

Read the stage instructions carefully.
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
