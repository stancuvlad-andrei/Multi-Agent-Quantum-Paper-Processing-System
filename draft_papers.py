import os
import time
from pathlib import Path
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY", "your_actual_api_key_here")
client = genai.Client(api_key=api_key)

MODEL_ID = "gemini-3.8-flash"

BASE_DIR = Path(__file__).parent
AGENTS_DIR = BASE_DIR / "Agents"
RESULTS_DIR = BASE_DIR / "Results"

def run_agent(system_md: str, user_content: str, max_retries=6) -> str:
    delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_md,
                    temperature=0.2,
                ),
            )
            return response.text.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Server busy (503/High Demand). Retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(delay)
            delay *= 2

def draft_solutions():
    writer_md = (AGENTS_DIR / "06_paper_writer.md").read_text(encoding="utf-8")
    
    for txt_file in sorted(RESULTS_DIR.glob("*_results.txt")):
        print(f"Drafting solution based on: {txt_file.name}...")
        compiled_data = txt_file.read_text(encoding="utf-8")
        drafted_paper = run_agent(writer_md, compiled_data)
        
        draft_out_path = RESULTS_DIR / txt_file.name.replace("_results.txt", "_solution_draft.txt")
        draft_out_path.write_text(drafted_paper, encoding="utf-8")
        print(f"Saved Draft -> {draft_out_path}")

if __name__ == "__main__":
    draft_solutions()