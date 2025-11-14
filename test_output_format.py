"""
Test script to verify the new structured output format.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.app.schemas import (
    SummarizeResponse, RevisionResponse, AskResponse,
    BilingualResponse, RevisionQuestionResponse
)

def test_summarize_response():
    """Test /summarize response format."""
    response = BilingualResponse(
        english="Chapter 1 covers the fundamentals of biology.",
        swahili="Sura ya 1 inafunika misingi ya biolojia."
    )
    summary = SummarizeResponse(chapter="1", response=response)
    print("/summarize response format:")
    print(summary.model_dump_json(indent=2))
    print()

def test_revision_response():
    """Test /revision response format."""
    questions = [
        RevisionQuestionResponse(
            question_text="What are the main components of a cell?",
            answer=BilingualResponse(
                english="The main components include the nucleus, cytoplasm, and cell membrane.",
                swahili="Sehemu kuu zinajumuisha kiini, sitoplazma, na kiambatanisho cha seli."
            )
        ),
        RevisionQuestionResponse(
            question_text="Describe mitosis.",
            answer=BilingualResponse(
                english="Mitosis is the process of cell division that produces two identical daughter cells.",
                swahili="Mitosis ni mchakato wa mgawanyiko wa seli unaozalisha seli mbili zinazofanana."
            )
        )
    ]
    revision = RevisionResponse(chapter="1", questions=questions)
    print("/revision response format:")
    print(revision.model_dump_json(indent=2))
    print()

def test_ask_response():
    """Test /ask response format."""
    response = BilingualResponse(
        english="Photosynthesis is the process by which plants convert light energy into chemical energy.",
        swahili="Umeme jua ni mchakato ambao mimea hubadilisha nishati ya mwanga kuwa nishati ya kemikali."
    )
    ask = AskResponse(
        question_text="What is photosynthesis?",
        response=response
    )
    print("/ask response format:")
    print(ask.model_dump_json(indent=2))
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Structured Output Formats")
    print("=" * 60)
    print()
    
    test_summarize_response()
    test_revision_response()
    test_ask_response()
    
    print("=" * 60)
    print("All response formats validated successfully!")
    print("=" * 60)
