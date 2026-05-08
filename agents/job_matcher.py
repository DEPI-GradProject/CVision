# agents/job_matcher.py

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from models.schemas import AgentState, Job, JobMatches
from utils.retriever import search_jobs
from dotenv import load_dotenv
import json

load_dotenv()

# سريع للـ Query Enhancement
llm_fast = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.1
)

# قوي للـ Match Scoring
llm_strong = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1
)

# Query Enhancement Prompt
query_prompt = PromptTemplate.from_template("""
You are a job search expert.
Convert the candidate's skills into a rich semantic search query for finding relevant jobs.

Candidate Skills: {skills}

Rules:
- Expand skills into related job titles and technologies
- Add relevant industry terms
- Keep it under 30 words
- Return the enhanced query only, no explanation

Enhanced Query:
""")

query_chain = query_prompt | llm_fast | StrOutputParser()

# Match Scoring Prompt
match_prompt = PromptTemplate.from_template("""
You are a job matching expert.

Candidate Skills: {skills}

Jobs Found:
{jobs}

For each job calculate:
- match_score (0-100): how well the candidate fits
- matched_skills: skills the candidate has that match the job
- missing_skills: skills required but candidate doesn't have
- reason: one sentence why this job fits

Return JSON only, no extra text:
{{
  "matched_jobs": [
    {{
      "title": "job title",
      "link": "job link",
      "skills": "job skills",
      "match_score": 85,
      "matched_skills": ["Python", "FastAPI"],
      "missing_skills": ["Docker"],
      "reason": "Great fit because..."
    }}
  ]
}}
""")

match_chain = match_prompt | llm_strong | StrOutputParser()

def job_matcher_agent(state: AgentState) -> AgentState:
    try:
        if state.analysis is None:
            state.error = "No analysis found, run cv_analyzer first"
            return state

        skills = ", ".join(state.analysis.skills_extracted)

        # Step 1: Query Enhancement
        enhanced_query = query_chain.invoke({"skills": skills})
        print(f"Enhanced Query: {enhanced_query}")

        # Step 2: Semantic Search with Enhanced Query
        raw_jobs = search_jobs(enhanced_query, k=10)

        jobs_text = ""
        for job in raw_jobs:
            jobs_text += f"Title: {job['title']}\n"
            jobs_text += f"Skills: {job['skills']}\n"
            jobs_text += f"Link: {job['link']}\n"
            jobs_text += "---\n"

        # Step 3: Match Scoring
        result = match_chain.invoke({
            "skills": skills,
            "jobs": jobs_text
        })

        clean = result
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        parsed = json.loads(clean)

        matched_jobs = [
            Job(
                title=j["title"],
                link=j["link"],
                skills=j["skills"],
                match_score=j.get("match_score"),
                matched_skills=j.get("matched_skills"),
                missing_skills=j.get("missing_skills"),
                reason=j.get("reason")
            )
            for j in parsed["matched_jobs"]
        ]

        state.job_matches = JobMatches(matched_jobs=matched_jobs)

    except Exception as e:
        state.error = f"Error matching jobs: {str(e)}"

    return state