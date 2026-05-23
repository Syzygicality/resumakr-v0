from pydantic import BaseModel, EmailStr, model_validator
from typing import List, Optional, Literal, Any
import re


class BulletPointMixin(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def insert_bolding(cls, data: Any) -> Any:
        if isinstance(data, dict) and "bullet_points" in data:
            data["bullet_points"] = [
                re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", bp)
                if isinstance(bp, str)
                else bp
                for bp in data["bullet_points"]
            ]
        return data


class Link(BaseModel):
    name: Optional[str] = None
    url: str


class SkillList(BaseModel):
    name: str
    skills: List[str]


class SkillSection(BaseModel):
    title: str = "Technical Skills"
    skill_lists: List[SkillList]


class ExperienceSubsection(BulletPointMixin, BaseModel):
    position: str
    company: str
    location: str = "Remote"
    start_date: str
    end_date: str = "Present"
    bullet_points: List[str] = []


class ExperienceSection(BaseModel):
    title: str = "Work Experience"
    experiences: List[ExperienceSubsection]


class ProjectSubsection(BulletPointMixin, BaseModel):
    name: str
    secondary_name: Optional[str] = None
    skills: List[str]
    link: Optional[Link] = None
    bullet_points: List[str] = []


class ProjectSection(BaseModel):
    title: str = "Projects"
    projects: List[ProjectSubsection]


class EducationSubsection(BaseModel):
    institution: str
    degree: str
    location: str
    start_date: Optional[str] = None
    end_date: str
    relevant_coursework: Optional[List[str]] = []
    gpa: Optional[float] = None


class EducationSection(BaseModel):
    title: str = "Education"
    educations: List[EducationSubsection]


class CertSubsection(BulletPointMixin, BaseModel):
    name: str
    issuer: str
    link: Optional[Link] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    bullet_points: List[str] = []


class CertSection(BaseModel):
    title: str = "Professional Certificates"
    certifications: List[CertSubsection]


class Resume(BaseModel):
    name: str
    phone_number: str
    email: EmailStr
    socials: Optional[List[Link]] = []
    section_order: List[Literal["education", "skills", "experience", "projects"]] = [
        "education",
        "skills",
        "experience",
        "projects",
        "certs",
    ]
    education: Optional[EducationSection] = None
    skills: Optional[SkillSection] = None
    experience: Optional[ExperienceSection] = None
    projects: Optional[ProjectSection] = None
    certs: Optional[CertSection] = None
