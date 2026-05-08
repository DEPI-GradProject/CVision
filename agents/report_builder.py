# agents/report_builder.py

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from models.schemas import AgentState
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3
)

parser = StrOutputParser()

prompt = PromptTemplate(
    template="""
You are a professional career advisor writing a comprehensive career report.

== CV ANALYSIS ==
Strengths:
{strengths}

Weaknesses:
{weaknesses}

Suggestions:
{suggestions}

Skills Found:
{skills}

== ATS SCORE ==
Overall ATS Score: {ats_score}/100
- Format Score: {format_score}/100
- Structure Score: {structure_score}/100
- Content Score: {content_score}/100
- Length Score: {length_score}/100

ATS Issues:
{ats_issues}

== TOP JOB MATCHES ==
{jobs}

Write a professional career report with these sections:

1. EXECUTIVE SUMMARY
   Brief overview of the candidate's profile and ATS score interpretation.

2. STRENGTHS
   Highlight the strong points found in the CV.

3. AREAS FOR IMPROVEMENT
   Address weaknesses and ATS issues clearly.

4. ATS OPTIMIZATION TIPS
   Specific actions to improve the ATS score based on the issues found.

5. TOP JOB MATCHES
   For each job explain:
   - Why it's a good fit (matched skills)
   - What skills to develop (missing skills)
   - Match score interpretation

6. ACTION PLAN
   3-5 concrete next steps the candidate should take.

Be specific, encouraging, and professional.
""",
    input_variables=[
        "strengths", "weaknesses", "suggestions", "skills",
        "ats_score", "format_score", "structure_score", "content_score", "length_score",
        "ats_issues", "jobs"
    ]
)

chain = prompt | llm | parser

def report_builder_agent(state: AgentState) -> AgentState:
    try:
        if state.analysis is None:
            state.error = "No analysis found, run cv_analyzer first"
            return state

        if state.job_matches is None:
            state.error = "No job matches found, run job_matcher first"
            return state

        ats = state.analysis.ats_result
        breakdown = ats.breakdown if ats else None

        jobs_text = ""
        for job in state.job_matches.matched_jobs:
            jobs_text += f"- {job.title}\n"
            jobs_text += f"  Match Score: {job.match_score}/100\n"
            jobs_text += f"  Matched Skills: {', '.join(job.matched_skills or [])}\n"
            jobs_text += f"  Missing Skills: {', '.join(job.missing_skills or [])}\n"
            jobs_text += f"  Reason: {job.reason}\n"
            jobs_text += f"  Link: {job.link}\n\n"

        result = chain.invoke({
            "strengths": "\n".join(state.analysis.strengths),
            "weaknesses": "\n".join(state.analysis.weaknesses),
            "suggestions": "\n".join(state.analysis.suggestions),
            "skills": ", ".join(state.analysis.skills_extracted),
            "ats_score": ats.ats_score if ats else "N/A",
            "format_score": breakdown.format if breakdown else "N/A",
            "structure_score": breakdown.structure if breakdown else "N/A",
            "content_score": breakdown.content if breakdown else "N/A",
            "length_score": breakdown.length if breakdown else "N/A",
            "ats_issues": "\n".join(ats.issues if ats else []),
            "jobs": jobs_text
        })

        state.final_report = result

    except Exception as e:
        state.error = f"Error building report: {str(e)}"

    return state