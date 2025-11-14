# ai_tutor/src/retrieve_answer.py

import os
import re
import warnings
from dotenv import load_dotenv
load_dotenv()

# Suppress telemetry and deprecation warnings
warnings.filterwarnings("ignore")

# LangChain imports
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import Runnable
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Project utilities
from utils.chapter_matcher import is_in_chapter
from utils.prompt_helpers import build_prompt_template, build_summary_prompt
from utils.revision_filter import extract_revision_questions
from utils.token_utils import estimate_tokens

# Load vector DB
vectorstore = Chroma(
    persist_directory="vector_db/bio_form1",
    embedding_function=OpenAIEmbeddings()
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.3)

# --- MAIN ---
if __name__ == "__main__":
    user_question = input("Ask a Biology question: ").strip()
    print(f"Received input: {user_question}")

    # 🧠 1. Chapter Summary
    summary_match = re.search(r"summarize\s+(?:chapter|chap)?\s*(\d+(\.\d+)*)", user_question.lower())
    if summary_match:
        print("Summary mode triggered")
        chapter_query = summary_match.group(1)

        all_docs = vectorstore.similarity_search("", k=9999)
        raw_chapter_docs = [
            doc for doc in all_docs
            if doc.metadata.get("type") == "content"
            and is_in_chapter(doc.metadata.get("chapter", ""), chapter_query)
            and len(doc.page_content.strip()) > 50
            and not re.match(r"^\W*$", doc.page_content.strip())
        ]

        raw_chapter_docs.sort(key=lambda d: len(d.page_content), reverse=True)

        selected_docs = []
        token_total = 0
        for doc in raw_chapter_docs:
            tokens = estimate_tokens(doc.page_content)
            if token_total + tokens > 13000:
                break
            selected_docs.append(doc)
            token_total += tokens

        print(f"Using {len(selected_docs)} chunks ({token_total} tokens) for summarization.")

        if selected_docs:
            summary_prompt = build_summary_prompt(chapter_query)
            summary_chain = create_stuff_documents_chain(llm=llm, prompt=summary_prompt)
            result = summary_chain.invoke({"context": selected_docs})
            print("Chapter Summary:\n")
            print(result)
        else:
            print("No content chunks found for Chapter", chapter_query)
        exit()

    # 📘 2. Revision Question Answering
    revision_match = re.search(
        r"(?:revision questions|revision)?\s*(?:for)?\s*(?:chapter|chap)?\s*(\d+(\.\d+)*)",
        user_question.lower()
    )

    if "revision" in user_question.lower() and revision_match:
        print("Revision mode triggered")
        chapter_query = revision_match.group(1)

        all_docs = vectorstore.similarity_search("", k=9999)

        # Split into content and revision docs
        content_docs = [
            doc for doc in all_docs
            if doc.metadata.get("type") == "content"
            and is_in_chapter(doc.metadata.get("chapter", ""), chapter_query)
        ]
        revision_docs = [
            doc for doc in all_docs
            if doc.metadata.get("type") == "revision"
            and is_in_chapter(doc.metadata.get("chapter", ""), chapter_query)
        ]

        for doc in revision_docs:
            print(f"Found revision chunk: Chapter {doc.metadata.get('chapter')} | {doc.page_content[:60]}...")

        questions = extract_revision_questions(revision_docs)
        questions = list(dict.fromkeys(questions))  # Deduplicate

        if questions:
            prompt = build_prompt_template(chapter_query)
            chain = create_stuff_documents_chain(llm=llm, prompt=prompt)

            for idx, q in enumerate(questions):
                # Try to match the question to the most relevant content chunks
                relevant_docs = [
                    doc for doc in content_docs
                    if any(word in doc.page_content.lower() for word in q.lower().split())
                ]

                # Fallback to first few chunks if no match
                if not relevant_docs:
                    relevant_docs = content_docs[:3]

                print(f"\nRevision Question {idx+1}: {q}")
                result = chain.invoke({
                    "context": relevant_docs,
                    "input": q
                })
                print("Answer:\n", result)
        else:
            print("No revision questions found for Chapter", chapter_query)
        exit()

    # 💬 3. General Question Answering
    print("General question mode triggered")
    prompt = build_prompt_template("unknown")
    qa_chain: Runnable = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=create_stuff_documents_chain(llm=llm, prompt=prompt)
    )

    result = qa_chain.invoke({"input": user_question})
    print("\nAnswer:\n")
    print(result["answer"])

    print("\nRetrieved Chunks:\n")
    for doc in result.get("context", []):
        print(f"• Chapter: {doc.metadata.get('chapter')} | Type: {doc.metadata.get('type')}")
