import os
import time
from pathlib import Path
from pypdf import PdfReader
from google import genai
from google.genai import types

# Initialize client
client = genai.Client()
MODEL_ID = "gemini-3.8-flash"

BASE_DIR = Path(__file__).parent
AGENTS_DIR = BASE_DIR / "Agents"
PAPERS_DIR = BASE_DIR / "Papers"
RESULTS_DIR = BASE_DIR / "Results"

def load_agent_prompt(filename: str) -> str:
    return (AGENTS_DIR / filename).read_text(encoding="utf-8")

def read_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def run_agent(system_md: str, user_content: str, max_retries=5) -> str:
    delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_md,
                    temperature=0.1,
                ),
            )
            return response.text.strip()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Server busy (503/Rate limit). Retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
            time.sleep(delay)
            delay *= 2

def process_papers():
    # Ensure Results is a directory
    if RESULTS_DIR.is_file():
        RESULTS_DIR.unlink()
    RESULTS_DIR.mkdir(exist_ok=True)

    # Load all .md agent definitions
    reader_md = load_agent_prompt("01_paper_reader.md")
    abstract_md = load_agent_prompt("02_abstract_extractor.md")
    keywords_md = load_agent_prompt("03_keyword_extractor.md")
    questions_md = load_agent_prompt("04_open_questions_extractor.md")
    compiler_md = load_agent_prompt("05_txt_compiler.md")

    for pdf_file in sorted(PAPERS_DIR.glob("*.pdf")):
        print(f"Processing: {pdf_file.name}...")
        raw_text = read_pdf_text(pdf_file)

        # 1. Reader Agent structures the paper
        structured_paper = run_agent(reader_md, raw_text)

        # 2. Specialist Agents extract target sections
        abstract = run_agent(abstract_md, structured_paper)
        keywords = run_agent(keywords_md, structured_paper)
        open_questions = run_agent(questions_md, structured_paper)

        # 3. Compiler Agent formats the final .txt output
        combined_input = (
            f"SOURCE FILE: {pdf_file.name}\n\n"
            f"STRUCTURED PAPER:\n{structured_paper}\n\n"
            f"EXTRACTED ABSTRACT:\n{abstract}\n\n"
            f"EXTRACTED KEYWORDS:\n{keywords}\n\n"
            f"EXTRACTED OPEN QUESTIONS:\n{open_questions}"
        )
        final_txt = run_agent(compiler_md, combined_input)

        # Save to Results/<paper_name>.txt
        out_path = RESULTS_DIR / f"{pdf_file.stem}_results.txt"
        out_path.write_text(final_txt, encoding="utf-8")
        print(f"Saved -> {out_path}")

if __name__ == "__main__":
    process_papers()