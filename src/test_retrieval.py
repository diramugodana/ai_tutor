# src/test_retrieval.py

import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import Pinecone as LangchainPinecone
from pinecone import Pinecone as PineconeClient

from langchain.chains.retrieval_qa.base import RetrievalQA

# Load env
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
index_name = os.getenv("PINECONE_INDEX_NAME")

# ✅ Init Pinecone SDK client + index object
pc = PineconeClient(api_key=pinecone_api_key)
index = pc.Index(index_name)

# ✅ Init LangChain wrapper
embeddings = OpenAIEmbeddings()
vectorstore = LangchainPinecone(
    index=index,
    embedding=embeddings,
    text_key="text"  # ✅ This tells LangChain where to look
)
# ✅ Build LLM-powered QA chain
llm = ChatOpenAI(temperature=0.2)
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())

# 🔍 Ask a test question
question = "What is osmosis in biology?"
print(f"\n❓ Question: {question}")

answer = qa_chain.run(question)
print(f"\n✅ Answer:\n{answer}")
