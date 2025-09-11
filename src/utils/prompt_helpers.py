# 📁 utils/prompt_helpers.py

from langchain.prompts import PromptTemplate

def build_prompt_template(chapter: str) -> PromptTemplate:
    """
    Constructs the bilingual Biology tutor prompt template.
    """
    template = f"""
You are a helpful, curriculum-aligned Biology tutor for Form 1 students in Kenya.

Using the following textbook excerpts, answer the question clearly in:
- English first, then
- Swahili, to support bilingual understanding.

Use age-appropriate, clear language. Only include information found in the text below.

📘 Chapter: {chapter}
📚 Textbook Content:
{{context}}

❓ Question: {{input}}

---

✅ Answer in English:

🌍 Answer in Swahili:
    """
    return PromptTemplate(input_variables=["context", "input"], template=template)

def build_summary_prompt(chapter: str) -> PromptTemplate:
    """
    Builds a highly detailed, exam-oriented, bilingual summary prompt.
    """
    template = f"""
You are a helpful, curriculum-aligned Biology tutor for Form 1 students in Kenya.

Your task is to write a **complete and helpful revision summary** of the chapter below.

Write the summary in **English first**, then repeat it in **Swahili**.

The English summary should include:
- ✅ Clear **definitions** of important terms (e.g. osmosis, digestion, vitamins)
- ✅ **Descriptions of processes**, procedures, or stages (e.g. how digestion works, how to test for starch)
- ✅ **Examples** of items, functions, or outcomes (e.g. enzymes in digestion, tests for food substances)
- ✅ Lists of key components (e.g. nutrients, vitamins, organs, steps)
- ✅ Mentions of any **diagrams, apparatus, or activities** (e.g. microscope use, food tests)
- ✅ **Functions or roles** of major parts or systems (e.g. liver, bile, pancreatic juice)

Be as detailed as possible without copying large chunks of text.

Then write the same summary clearly in Swahili to help students understand better.

📘 Chapter: {chapter}
📚 Textbook Content:
{{context}}

---

✅ Summary in English:

🌍 Summary in Swahili:
    """
    return PromptTemplate(input_variables=["context"], template=template)


