from pydantic import BaseModel, EmailStr

from typing import List, Optional, Literal


class Link(BaseModel):
    name: Optional[str] = None
    url: str


class SkillList(BaseModel):
    name: str
    skills: List[str]


class SkillSection(BaseModel):
    title: str = "Technical Skills"
    skill_lists: List[SkillList]


class ExperienceSubSection(BaseModel):
    position: str
    company: str
    location: str = "Remote"
    start_date: str
    end_date: str = "Present"
    bullet_points: List[str]


class ExperienceSection(BaseModel):
    title: str = "Work Experience"
    experiences: List[ExperienceSubSection]


class ProjectSubSection(BaseModel):
    name: str
    secondary_name: Optional[str] = None
    skills: List[str]
    link: Optional[Link] = None
    bullet_points: List[str]


class ProjectSection(BaseModel):
    title: str = "Projects"
    projects: List[ProjectSubSection]


class EducationSubSection(BaseModel):
    institution: str
    degree: str
    location: str
    start_date: Optional[str] = None
    end_date: str
    relevant_coursework: Optional[List[str]] = []
    gpa: Optional[float]


class EducationSection(BaseModel):
    title: str = "Education"
    educations: List[EducationSubSection]


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
    ]
    education: Optional[EducationSection] = None
    skills: Optional[SkillSection] = None
    experience: Optional[ExperienceSection] = None
    projects: Optional[ProjectSection] = None
