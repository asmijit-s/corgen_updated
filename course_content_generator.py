# course_content_generator.py

import os
import re
import json
import requests
from typing import List, Dict, Union, Optional, Type
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel
import PyPDF2
from google import genai
from google.genai.types import GenerateContentConfig, Content

# Load environment
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

# ----------------------------- Constants -----------------------------
MAX_CHARS_PER_CONTEXT = 12000

# ----------------------------- Utility Functions -----------------------------

def read_file(path: str, mode: str = "r", encoding: Optional[str] = "utf-8") -> str:
    try:
        with open(path, mode, encoding=encoding) as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")

def scrape_text_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style"]):
            tag.extract()
        return soup.get_text(separator="\n").strip()
    except Exception as e:
        raise ValueError(f"Failed to scrape URL '{url}': {e}")

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'https?://\S{80,}', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def truncate_text(text: str, max_chars: int = MAX_CHARS_PER_CONTEXT) -> str:
    return text[:max_chars] if len(text) > max_chars else text

# ----------------------------- LLM Interaction -----------------------------

def call_gemini(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw = response.text.strip() if response.text else ""
    return re.sub(r'^```(?:json)?|```$', '', raw.strip())

# ----------------------------- Prompt Helpers -----------------------------

def summarize_text_with_gemini(text: str, label: str) -> str:
    if not text.strip():
        return ""
    prompt = f"""
You are a concise summarizer.
Summarize the following {label} in simple bullet points. Avoid examples or repetition.
{text[:MAX_CHARS_PER_CONTEXT]}
"""
    return call_gemini(prompt)

def course_outline_to_text(outline: Union[dict, List[dict]]) -> str:
    if isinstance(outline, dict):
        return "\n".join([f"- {k}: {v}" for k, v in outline.items()])
    elif isinstance(outline, list):
        return "\n".join([f"- {item['module']}: {item['description']}" for item in outline])
    return str(outline)

def submodules_to_bullets(submodules: List[Dict[str, str]]) -> str:
    return "\n".join([f"- {item['submoduleName']}: {item['submoduleDescription']}" for item in submodules])

# ----------------------------- Pydantic Models -----------------------------

class ReadingInput(BaseModel):
    course_outline: Union[dict, List[dict]]
    module_name: str
    submodule_name: str
    user_prompt: str
    previous_material_summary: str
    notes_path: Optional[str] = None
    pdf_path: Optional[str] = None
    url: Optional[str] = None

class LectureInput(BaseModel):
    course_outline: Union[dict, List[dict]]
    module_name: str
    submodule_name: str
    user_prompt: str
    prev_activities_summary: str
    notes_path: Optional[str] = None
    pdf_path: Optional[str] = None
    text_examples: Optional[Union[str, List[str]]] = None
    duration_minutes: Optional[int] = None

class QuizInput(BaseModel):
    module_name: str
    submodule_name: str
    material_summary: str  # Lecture script or reading material summary of this submodule
    number_of_questions: int
    quiz_type: str  # "MCQ" or "T/F"
    total_score: int
    user_prompt: str

class AssignmentInput(BaseModel):
    module_name: str
    submodule_name: str
    user_prompt: str
    all_submodule_summaries: List[Dict[str, str]]

class MindmapInput(BaseModel):
    module_name: str
    submodule_summaries: List[Dict[str, str]]


class QuizOut(BaseModel):
    question: str
    options: Union[List[str], None] = None  # For MCQs
    answer: str
    explanation: str
# ----------------------------- Content Generators -----------------------------

def generate_reading_material(course_outline, module_name, submodule_name, user_prompt,
                               previous_material_summary, notes_path=None, pdf_path=None, url=None):
    notes_text = clean_text(read_file(notes_path)) if notes_path else ""
    pdf_text = clean_text(extract_text_from_pdf(pdf_path)) if pdf_path else ""
    url_text = clean_text(scrape_text_from_url(url)) if url else ""

    summarized_notes = summarize_text_with_gemini(notes_text, label="lecture notes") if notes_text else ""
    summarized_pdf = summarize_text_with_gemini(pdf_text, label="PDF reading") if pdf_text else ""
    summarized_url = summarize_text_with_gemini(url_text, label="web article") if url_text else ""

    combined_context = "\n\n".join(filter(None, [
        f"--- Summary from Notes ---\n{summarized_notes}",
        f"--- Summary from PDF ---\n{summarized_pdf}",
        f"--- Summary from URL ---\n{summarized_url}"
    ]))

    combined_context = truncate_text(combined_context)

    prompt = f"""
You are an expert Math/Data Analyst/Machine Learning/Deep Learning/Generative AI educator.
Create **reading material** for a submodule. Ensure:
- Alignment with course outline
- Avoid redundancy with previous materials
- Friendly tone, examples, code snippets, and illustrations
- Clear connection to course progression

### Input:
Course Outline:
{course_outline_to_text(course_outline)}

Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
Previous Summary: {previous_material_summary}
Context:
{combined_context or 'No additional context provided.'}

### Output Format:
Markdown passage with:
- Clear structure, explanations, examples
- Code, math, applications
- Suggested visuals
- Ending summary
"""

    final_material = call_gemini(prompt)

    summary_prompt = f"""
Summarize the following reading material in concise bullet points:
{final_material}
"""
    material_summary = call_gemini(summary_prompt)

    return {
        "readingMaterial": final_material,
        "readingMaterialSummary": material_summary
    }, {
        "notesSummary": summarized_notes,
        "pdfSummary": summarized_pdf,
        "urlSummary": summarized_url
    }

def generate_lecture_script(course_outline, module_name, submodule_name, user_prompt,
                            prev_activities_summary, notes_path=None, pdf_path=None,
                            text_examples=None, duration_minutes=None):

    notes_text = read_file(notes_path) if notes_path else ""
    pdf_text = extract_text_from_pdf(pdf_path) if pdf_path else ""
    examples_text = "\n".join(text_examples) if isinstance(text_examples, list) else (text_examples or "")

    prompt = f"""
You are a skilled educator and video content designer.
Create a **lecture script** with:
- Conversational tone, structure, and hooks
- Speaker notes, explanation points
- Duration: {duration_minutes or 'Unspecified'} minutes

### Input:
Course Outline:
{course_outline_to_text(course_outline)}
Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
Previous Summary:
{prev_activities_summary}

Notes:
{notes_text or 'None'}
PDF:
{pdf_text or 'None'}
Examples:
{examples_text or 'None'}

### Output Format:
Markdown lecture script with speaker cues and segment summaries
"""
    return call_gemini(prompt)

def generate_quiz(module_name: str, submodule_name: str, material_summary: str,
                  number_of_questions: int, quiz_type: str, total_score: int,
                  user_prompt: str) -> List[Dict]:

    prompt = f"""
You are a quiz designer for an educational AI system.

### Task:
Generate a quiz for the **submodule** "{submodule_name}" under the module "{module_name}". Use the following content source:

### Material Summary:
{material_summary}

### Guidelines:
- Create exactly {number_of_questions} questions.
- Quiz Type: {quiz_type}
- Total Score: {total_score} (distribute marks equally).
- Follow this user instruction: {user_prompt}
- Each question must include a short explanation of the correct answer.
- Questions should be beginner-friendly and test conceptual clarity.

### Output Format:
Return a **JSON array** where each item follows this schema:
{{
  "question": "<question_text>",
  "options": ["<A>", "<B>", "<C>", "<D>"],  # Omit if T/F
  "answer": "<correct_option>",  # "A", "B", "C", "D" or "True"/"False"
  "explanation": "<why this is the correct answer>"
}}

### Rules:
- For **MCQ**, provide exactly 4 options and one correct answer.
- For **T/F**, avoid ambiguity and give direct true/false questions.
- Only return the JSON array. No markdown or comments.
"""

    response = call_gemini(prompt)
    try:
        if response.startswith("```json"):
            response = response.strip("```json").strip("```").strip()
        return json.loads(response)
    except Exception as e:
        raise ValueError(f"Quiz JSON parsing failed: {e}")


def generate_assignment(module_name, submodule_name, user_prompt, all_submodule_summaries):
    prompt = f"""
You are a course designer. Create an **assignment** based on submodule summaries.
It should integrate concepts and assess practical + theoretical understanding.

### Input:
Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
Submodule Summaries:
{submodules_to_bullets(all_submodule_summaries)}

### Output:
Markdown with Title, Description, Objectives, Deliverables, Evaluation Criteria
"""
    return call_gemini(prompt)

def generate_mindmap(module_name, submodule_summaries):
    prompt = f"""
You are a mind map generator.
Create a **mind map** from submodule summaries in nested bullet point style.

### Input:
Module: {module_name}
Summaries:
{submodules_to_bullets(submodule_summaries)}

### Output:
Markdown nested bullet point map
"""
    return call_gemini(prompt)
