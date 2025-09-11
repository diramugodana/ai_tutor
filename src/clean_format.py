import os
import json
import re

RAW_TEXT_PATH = "data/extracted_text/bio_form1_raw.txt"
OUTPUT_JSON_PATH = "data/cleaned_chunks/bio_form1_structured.json"

def clean_and_structure_text():
    with open(RAW_TEXT_PATH, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = raw_text.splitlines()
    structured = []

    current_chapter = None
    current_text_block = []
    is_revision = False

    for line in lines:
        line = line.strip()

        # Detect chapter/subchapter headers like "1.1", "1.2"
        chapter_match = re.match(r"^(\d{1,2}\.\d{1,2})", line)
        if chapter_match:
            # Save previous block
            if current_text_block:
                structured.append({
                    "chapter": current_chapter,
                    "type": "revision" if is_revision else "content",
                    "text": current_text_block if is_revision else " ".join(current_text_block)
                })
                current_text_block = []
                is_revision = False

            current_chapter = chapter_match.group(1)
            continue

        # Detect revision blocks
        if "revision questions" in line.lower():
            if current_text_block:
                structured.append({
                    "chapter": current_chapter,
                    "type": "content",
                    "text": " ".join(current_text_block)
                })
                current_text_block = []
            is_revision = True
            continue

        # Accumulate non-empty lines
        if line:
            current_text_block.append(line)

    # Save final block
    if current_text_block:
        structured.append({
            "chapter": current_chapter,
            "type": "revision" if is_revision else "content",
            "text": current_text_block if is_revision else " ".join(current_text_block)
        })

    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)

    print(f"✅ Structured {len(structured)} content blocks. Saved to: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    clean_and_structure_text()

