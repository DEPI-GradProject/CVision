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

prompt = PromptTemplate(
    template="""
You are a professional career advisor writing a personalized career report.

== CANDIDATE PROFILE ==
Experience Level: {experience_level}
Years of Experience: {years_of_experience} years
Target Job Title: {target_job_title}

== CV ANALYSIS ==
Strengths: {strengths}
Weaknesses: {weaknesses}
Suggestions: {suggestions}
Skills Found: {skills}

== ATS SCORE ==
Overall ATS Score: {ats_score}/100
- Format: {format_score}/100
- Structure: {structure_score}/100
- Content: {content_score}/100
- Length: {length_score}/100
ATS Issues: {ats_issues}

== TOP JOB MATCHES ==
{jobs}

Write a highly personalized career report for a {experience_level} level candidate targeting {target_job_title} roles with {years_of_experience} years of experience.

Include these sections:

1. EXECUTIVE SUMMARY
   Write a personalized 3-4 sentence summary specific to this candidate's level and target role.
   Mention their experience level, key strengths, and ATS score interpretation.

2. STRENGTHS
   Highlight strong points relevant to {target_job_title} roles.

3. AREAS FOR IMPROVEMENT
   Address weaknesses and ATS issues specific to their level.

4. ATS OPTIMIZATION TIPS
   Specific actions to improve the ATS score.

5. TOP JOB MATCHES
   For each job:
   - Match score and why
   - Matched vs missing skills
   - Whether the role fits their {experience_level} level

6. ACTION PLAN
   3-5 concrete next steps tailored to a {experience_level} targeting {target_job_title}.

Be specific, encouraging, and personalized. Avoid generic advice.
""",
    input_variables=[
        "experience_level", "years_of_experience", "target_job_title",
        "strengths", "weaknesses", "suggestions", "skills",
        "ats_score", "format_score", "structure_score", "content_score", "length_score",
        "ats_issues", "jobs"
    ]
)

chain = prompt | llm | StrOutputParser()

def report_builder_agent(state: AgentState) -> AgentState:
    try:
        if state.analysis is None:
            state.error = "No analysis found, run cv_analyzer first"
            return state

        if state.job_matches is None:
            state.error = "No job matches found, run job_matcher first"
            return state

        analysis = state.analysis
        ats = analysis.ats_result
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
            "experience_level": analysis.experience_level or "Junior",
            "years_of_experience": analysis.years_of_experience or 0,
            "target_job_title": analysis.target_job_title or "Software Developer",
            "strengths": "\n".join(analysis.strengths),
            "weaknesses": "\n".join(analysis.weaknesses),
            "suggestions": "\n".join(analysis.suggestions),
            "skills": ", ".join(analysis.skills_extracted),
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