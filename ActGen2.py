import requests
from bs4 import BeautifulSoup
import PyPDF2
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Union
from pydantic import BaseModel
from google import genai
import os
import json
from dotenv import load_dotenv
import PyPDF2
import re

# Load Gemini API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

# ----------------------------- Helpers -----------------------------

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {e}")

def extract_text_from_txt(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        raise ValueError(f"Failed to read text file: {e}")
    
def scrape_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text(separator="\n").strip()
    except Exception as e:
        raise ValueError(f"Failed to scrape URL '{url}': {e}")
    
MAX_CHARS_PER_CONTEXT = 12000  # Roughly 3000 tokens for Gemini Flash

def clean_text(text):
    if not text:
        return ""
    
    # Remove multiple spaces, newlines
    text = re.sub(r'\s+', ' ', text)
    
    # Remove URLs longer than 80 characters (likely junk)
    text = re.sub(r'https?://\S{80,}', '', text)
    
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()

def truncate_text(text, max_chars=MAX_CHARS_PER_CONTEXT):
    return text[:max_chars] if len(text) > max_chars else text    

def summarize_text_with_gemini(text: str, label: str = "content"):
    if not text.strip():
        return ""
    
    short_prompt = f"""
You are a concise summarizer.

Summarize the following {label} in simple, clear bullet points that cover key ideas only.
Avoid examples or repetition. Keep it factual and brief.

{text[:MAX_CHARS_PER_CONTEXT]}  # Truncate to avoid LLM crash
"""
    try:
        return call_gemini(short_prompt)
    except Exception as e:
        return f"(Failed to summarize {label})"



def course_outline_to_text(outline):
    if isinstance(outline, dict):
        return "\n".join([f"- {k}: {v}" for k, v in outline.items()])
    elif isinstance(outline, list):
        return "\n".join([f"- {item['module']}: {item['description']}" for item in outline])
    else:
        return str(outline)

def submodules_to_bullets(submodules):
    return "\n".join([f"- {item['submoduleName']}: {item['submoduleDescription']}" for item in submodules])

def call_gemini(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw_text = response.text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("```json").strip("```").strip()
    return raw_text

# ----------------------------- Models -----------------------------

class ReadingInput(BaseModel):
    course_outline: Union[dict, List[dict]]
    module_name: str
    submodule_name: str
    user_prompt: str
    previous_material_summary: str
    notes_path: Union[str, None] = None
    pdf_path: Union[str, None] = None
    url: Union[str, None] = None

class LectureInput(BaseModel):
    course_outline: Union[dict, List[dict]]
    module_name: str
    submodule_name: str
    user_prompt: str
    prev_activities_summary: str
    notes_path: Union[str, None] = None
    pdf_path: Union[str, None] = None
    text_examples: Union[str, List[str], None] = None
    duration_minutes: Union[int, None] = None

class QuizInput(BaseModel):
    module_name: str
    submodule_1: str
    summary_1: str
    submodule_2: str
    summary_2: str
    user_prompt: str

class AssignmentInput(BaseModel):
    module_name: str
    submodule_name: str
    user_prompt: str
    all_submodule_summaries: List[Dict[str, str]]

class MindmapInput(BaseModel):
    module_name: str
    submodule_summaries: List[Dict[str, str]]

# ----------------------------- Generators -----------------------------

def generate_reading_material(course_outline, module_name, submodule_name, user_prompt,
                               previous_material_summary, notes_path=None, pdf_path=None, url=None):
    # Extract + Clean
    notes_text = clean_text(extract_text_from_txt(notes_path)) if notes_path else ""
    pdf_text = clean_text(extract_text_from_pdf(pdf_path)) if pdf_path else ""
    url_text = clean_text(scrape_text_from_url(url)) if url else ""

    summarized_notes = summarize_text_with_gemini(notes_text, label="lecture notes") if notes_text else ""
    summarized_pdf = summarize_text_with_gemini(pdf_text, label="PDF reading") if pdf_text else ""
    summarized_url = summarize_text_with_gemini(url_text, label="web article") if url_text else ""

    combined_context = "\n\n".join([
       f"--- Summary from Notes ---\n{summarized_notes}" if summarized_notes else "",
       f"--- Summary from PDF ---\n{summarized_pdf}" if summarized_pdf else "",
       f"--- Summary from URL ---\n{summarized_url}" if summarized_url else ""
    ]).strip()


    combined_context = truncate_text(combined_context, MAX_CHARS_PER_CONTEXT)

    # Prompt to Gemini
    prompt = f"""
You are an expert Math/Data Analyst/Machine Learning/Deep Learning/Generative AI educator.

Your task is to create **reading material** for a specific submodule of a course which will be learnt by students. Ensure that the content:
- Aligns with the course outline
- Avoids repeating earlier reading materials
- Is in line with the previous submodules' summary
- Is beginner-friendly and engaging
- Utilizes provided context from notes, PDFs, or reference websites
- Adheres to the user's style or tone preferences
- Avoids and foul language or Obscenity

### Input:

Course Outline:
{course_outline_to_text(course_outline)}

Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
Previous Material Summary: {previous_material_summary}

Context from Notes, PDF, or URL:
{combined_context if combined_context else 'No additional context provided.'}

### Output Format:
Return a well-written **reading passage** in markdown format.
Provide a clear, engaging explanation of the submodule topic.
Provide examples, analogies, or illustrations where appropriate.
Give a brief summary at the end.
Show how this submodule connects to the overall course.
Include Code Snippets or mathematical formulas if relevant for better understanding.
Give practical applications or real-world relevance.
Tell the user what and where the can insert imgaes/graphs to illustrate concepts.
Use beginner-friendly language, examples, and logical structure.

"""
    return call_gemini(prompt), {
        "notesSummary": summarized_notes,
        "pdfSummary": summarized_pdf,
        "urlSummary": summarized_url
    }


def generate_lecture_script(course_outline, module_name, submodule_name, user_prompt,
                            prev_activities_summary, notes_path=None, pdf_path=None,
                            text_examples=None, duration_minutes=None):

    notes_text = extract_text_from_txt(notes_path) if notes_path else ""
    pdf_text = extract_text_from_pdf(pdf_path) if pdf_path else ""

    examples_text = "\n".join(text_examples) if isinstance(text_examples, list) else (text_examples or "")

    prompt = f"""
You are a skilled educator and video content designer.

Create a **lecture script** for the following submodule. The script will be used for a video-based lesson. Consider:
- Making it engaging, structured, and conversational
- Incorporating any provided notes, PDFs, or example text
- Adapting the content to the target duration

### Inputs:

Course Outline:
{course_outline_to_text(course_outline)}

Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
Target Duration: {duration_minutes or 'Not specified'} minutes

Summaries of Last 3 Activities:
{prev_activities_summary}

Notes Text:
{notes_text or 'None'}

PDF Extracted Text:
{pdf_text or 'None'}

Text Examples:
{examples_text or 'None'}

### Output Format:
Return a detailed **lecture script** in markdown format.
Include:
- Speaker Notes
- Explanation Points
- Examples
- Hooks and Summarizing Closures
"""
    return call_gemini(prompt)

def generate_quiz(module_name, submodule_1, summary_1, submodule_2, summary_2, user_prompt):
    prompt = f"""
You are a expert Math/Data Analyst/Machine Learning/Deep Learning/Generative AI assessment designer.

Generate a **quiz** focusing on the three recent submodules(You can also include questions from even before submodules sometime). Make sure questions test understanding of key concepts, are diverse in type (MCQ, True/False, Fill in the Blank), and are not overly complex.

### Input:
Module: {module_name}
Submodule 1: {submodule_1}
Summary 1: {summary_1}
Submodule 2: {submodule_2}
Summary 2: {summary_2}
User Prompt: {user_prompt}

### Output Format:
Return a JSON array of objects with:
- "question"
- "options" (for MCQs)
- "answer"
- "type" (MCQ, T/F, Short Answer)
"""
    return call_gemini(prompt)

def generate_assignment(module_name, submodule_name, user_prompt, all_submodule_summaries):
    prompt = f"""
You are a course designer.

Create an **assignment** for a submodule within a module. Use all submodule summaries in the module to design an integrative task. The assignment should assess both practical and conceptual understanding.

### Input:
Module: {module_name}
Submodule: {submodule_name}
User Prompt: {user_prompt}
All Submodule Summaries:
{submodules_to_bullets(all_submodule_summaries)}

### Output Format:
Return in markdown:
- Assignment Title
- Description
- Objectives
- Deliverables
- Evaluation Criteria
"""
    return call_gemini(prompt)

def generate_mindmap(module_name, submodule_summaries):
    prompt = f"""
You are a mind mapping assistant.

Create a **mind map** for a module using its submodules and their summaries. Capture main themes, concepts, and interrelationships. Use nested bullet format to represent branches.

### Input:
Module: {module_name}
Submodules and Summaries:
{submodules_to_bullets(submodule_summaries)}

### Output Format:
Return markdown-style mind map using bullet points and indentation.
"""
    return call_gemini(prompt)

# ----------------------------- API Endpoints -----------------------------

@app.post("/generate-reading-material")
def api_reading(input: ReadingInput):
    try:
        result, summaries = generate_reading_material(
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
            "readingMaterial": result,
            "sourceSummaries": summaries  # Show all intermediate summaries
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-lecture-script")
def api_lecture(input: LectureInput):
    try:
        result = generate_lecture_script(
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
        return {"lectureScript": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quiz")
def api_quiz(input: QuizInput):
    try:
        result = generate_quiz(
            module_name=input.module_name,
            submodule_1=input.submodule_1,
            summary_1=input.summary_1,
            submodule_2=input.submodule_2,
            summary_2=input.summary_2,
            user_prompt=input.user_prompt
        )
        return {"quiz": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-assignment")
def api_assignment(input: AssignmentInput):
    try:
        result = generate_assignment(
            module_name=input.module_name,
            submodule_name=input.submodule_name,
            user_prompt=input.user_prompt,
            all_submodule_summaries=input.all_submodule_summaries
        )
        return {"assignment": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-mindmap")
def api_mindmap(input: MindmapInput):
    try:
        result = generate_mindmap(
            module_name=input.module_name,
            submodule_summaries=input.submodule_summaries
        )
        return {"mindmap": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    course_outline = {
        "Supervised Learning": "Classification and regression using decision trees, logistic regression, and SVMs.",
        "Unsupervised Learning": "Clustering, dimensionality reduction, and anomaly detection."
    }

    module_name = "Supervised Learning"
    submodule_name = "Decision Trees"
    user_prompt = "Explain decision trees for high school students using analogies and minimal math."
    prev_activities_summary = "Previously, students learned about classification vs regression and basic ML models like linear regression."

    notes_path = "speech.txt"
    pdf_path = "attention.pdf"
    text_examples = [
        "A decision tree works like a flowchart to make decisions.",
        "At each step, it asks a question and splits the data based on the answer."
    ]
    duration_minutes = 12

    try:
        result = generate_lecture_script(
            course_outline=course_outline,
            module_name=module_name,
            submodule_name=submodule_name,
            user_prompt=user_prompt,
            prev_activities_summary=prev_activities_summary,
            notes_path=notes_path,
            pdf_path=pdf_path,
            text_examples=text_examples,
            duration_minutes=duration_minutes
        )

        print("\n✅ Generated Lecture Script:\n")
        print(result)

        # Save to JSON file
        with open("sample_lecture_script.json", "w", encoding="utf-8") as f:
            json.dump({"lecture_script": result}, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"❌ Error: {e}")
