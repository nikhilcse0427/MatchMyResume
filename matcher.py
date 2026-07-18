import os
from io import BytesIO
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pypdf import PdfReader
from docx import Document

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


load_dotenv()

my_api = os.getenv("GROQ_API_KEY")

if not my_api:
    raise ValueError("GROQ_API_KEY is missing in .env file")


llm = ChatGroq(
    api_key=my_api,
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)


class JobDescription(BaseModel):
    job_role: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    minimum_experience: int = 0
    educational_requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)


class Experience(BaseModel):
    company_name: str | None = None
    role: str | None = None
    duration: int = 0
    skills_used: List[str] = Field(default_factory=list)
    description: str = ""


class Resume(BaseModel):
    job_role: str | None = None
    name: str
    email: str | None = None
    total_experience_year: float | None = None
    experiences: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    candidate_name: str = Field(
        description="Full name of the candidate as mentioned in the resume"
    )
    matching_skills: List[str] = Field(
        default_factory=list,
        description="Skills from the resume that match the job description",
    )
    missing_skills: List[str] = Field(
        default_factory=list,
        description="Important skills required by the job but missing from the resume",
    )
    experience_requirement_met: bool = Field(
        description="True if candidate experience meets or exceeds minimum requirement"
    )
    match_score: float = Field(
        ge=0,
        le=100,
        description="Overall match percentage between resume and job description",
    )
    verdict: str = Field(
        description="Short final verdict such as Strong fit, Moderate fit, or Not suitable"
    )


JobDescription_parser = PydanticOutputParser(pydantic_object=JobDescription)
Resume_parser = PydanticOutputParser(pydantic_object=Resume)
MatchResult_parser = PydanticOutputParser(pydantic_object=MatchResult)


job_description_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert HR data extraction assistant.

Extract structured information from the given job description.

Rules:
- Only use information present in the text.
- Do not invent details.
- If a field is not mentioned, use an empty list or 0.
- Extract minimum experience as a number of years.

{format_instructions}
""",
        ),
        (
            "human",
            """
Job Description:

{job_description}
""",
        ),
    ]
).partial(format_instructions=JobDescription_parser.get_format_instructions())


job_description_chain = job_description_prompt | llm | JobDescription_parser


resume_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert resume parser.

Extract structured information from the candidate's resume.

Rules:
- Only use information explicitly present in the resume.
- Do not guess or invent details.
- If a field is missing, use null, 0, or an empty list.
- Extract experience duration in years whenever possible.

{format_instructions}
""",
        ),
        (
            "human",
            """
Resume Text:

{resume_text}
""",
        ),
    ]
).partial(format_instructions=Resume_parser.get_format_instructions())


resume_chain = resume_prompt | llm | Resume_parser


match_result_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert HR recruiter and resume screener.

Compare the candidate's resume against the job description.

Rules:
- Only use the provided structured data.
- Do not assume or invent information.
- Match skills carefully.
- Check whether the candidate's experience meets the minimum experience requirement.
- Give a fair match score from 0 to 100.

{format_instructions}
""",
        ),
        (
            "human",
            """
JOB DESCRIPTION:

{job_json}


CANDIDATE RESUME:

{resume_json}


Compare the candidate with the job description and provide the match assessment.
""",
        ),
    ]
).partial(format_instructions=MatchResult_parser.get_format_instructions())


match_result_chain = match_result_prompt | llm | MatchResult_parser


def read_pdf(source: Path | BytesIO) -> str:
    reader = PdfReader(source)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def read_docx(source: Path | BytesIO) -> str:
    document = Document(source)
    text = ""
    for para in document.paragraphs:
        if para.text.strip():
            text += para.text.strip() + "\n"
    return text.strip()


def read_resume(file_path: Path) -> str:
    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    if file_path.suffix.lower() == ".docx":
        return read_docx(file_path)
    raise ValueError("Only PDF and DOCX files are supported")


def read_resume_bytes(content: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    stream = BytesIO(content)

    if suffix == ".pdf":
        return read_pdf(stream)
    if suffix == ".docx":
        return read_docx(stream)

    raise ValueError("Only PDF and DOCX files are supported")


def parse_job_description(job_description: str) -> JobDescription:
    return job_description_chain.invoke({"job_description": job_description})


def parse_resume(resume_text: str) -> Resume:
    return resume_chain.invoke({"resume_text": resume_text})


def match_resume_with_job(
    job_data: JobDescription,
    resume_data: Resume,
) -> MatchResult:
    return match_result_chain.invoke(
        {
            "job_json": job_data.model_dump_json(),
            "resume_json": resume_data.model_dump_json(),
        }
    )


def screen_candidate(
    job_description: str,
    resume_content: bytes,
    resume_filename: str,
) -> dict:
    job_data = parse_job_description(job_description)
    resume_text = read_resume_bytes(resume_content, resume_filename)
    resume_data = parse_resume(resume_text)
    match_result = match_resume_with_job(job_data, resume_data)

    return {
        "job": job_data.model_dump(),
        "resume": resume_data.model_dump(),
        "match": match_result.model_dump(),
    }
