import os
import pytesseract
from pdf2image import convert_from_path

PDF_PATH = "data/raw_pdfs/KLB Bio Form 1.pdf"
OUTPUT_TXT = "data/extracted_text/bio_form1_raw.txt"

def extract_text_from_pdf(pdf_path, output_txt_path):
    print("🔄 Converting PDF to images...")
    pages = convert_from_path(pdf_path, dpi=300)

    print("🧠 Running OCR on each page...")
    full_text = ""
    for i, page in enumerate(pages):
        text = pytesseract.image_to_string(page, lang="eng")
        full_text += f"\n\n--- Page {i+1} ---\n\n{text}"
        print(f"✅ Processed page {i+1}")

    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(f"\n🎉 OCR complete! Text saved to: {output_txt_path}")

if __name__ == "__main__":
    extract_text_from_pdf(PDF_PATH, OUTPUT_TXT)
