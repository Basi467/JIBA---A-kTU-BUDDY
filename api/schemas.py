from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str = Field(min_length=6)
    scheme: str
    department: str
    semester: int


class RegisterResponse(BaseModel):
    user_id: int


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    scheme: str
    department: str
    semester: int


class LoginResponse(BaseModel):
    token: str
    user: UserOut


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

class SubjectOut(BaseModel):
    subject_code: str
    subject_name: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatMessageOut(BaseModel):
    role: str
    content: str


class ChatAskRequest(BaseModel):
    subject: str
    question: str
    topic: Optional[str] = None


class ChatAskResponse(BaseModel):
    reply: str


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

class ProgressOut(BaseModel):
    weak: List[str]
    completed: List[str]
    in_progress: List[str]
    progress_ratio: float


ProgressAction = Literal["viewed", "studied", "weak", "completed", "solved_pyq"]


class ProgressMarkRequest(BaseModel):
    subject: str
    topic: str
    action: ProgressAction


class ProgressMarkResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Exam mode
# ---------------------------------------------------------------------------

class ExamQuestionOut(BaseModel):
    year: Optional[int]
    marks: Optional[int]
    topic_name: Optional[str]
    question_text: str


class ModuleExamFocusOut(BaseModel):
    module_no: int
    high_priority_topics: List[str]
    medium_priority_topics: List[str]
    low_priority_topics: List[str]
    repeated_questions: List[ExamQuestionOut]


class TeachTopicItemOut(BaseModel):
    module_no: int
    topic_name: str
    priority_label: str
    question_count: Optional[int]
    weighted_score: Optional[float]


class TeachQuestionItemOut(BaseModel):
    module_no: int
    year: Optional[int]
    marks: Optional[int]
    topic_name: Optional[str]
    question_text: str


class TeachTopicRequest(BaseModel):
    subject: str
    topic: str


class TeachLessonOut(BaseModel):
    simple_explanation: str
    exam_answer: str
    key_points: List[str]
    memory_tip: str
    practice_question: str
    related_pyqs: List[ExamQuestionOut]


class AnswerQuestionRequest(BaseModel):
    subject: str
    question_text: str
    topic: Optional[str] = None


class AnswerQuestionResponse(BaseModel):
    answer: str


# ---------------------------------------------------------------------------
# Study plan
# ---------------------------------------------------------------------------

class StudyPlanRequest(BaseModel):
    subject: str
    exam_date: str
    hours_per_day: float
    manual_weak_topics: Optional[List[str]] = None


class StudyPlanItemOut(BaseModel):
    plan_date: str
    subject_name: str
    module_no: int
    topic_id: int
    topic_name: str
    priority_label: str
    question_count: int
    weighted_score: float
    recommended_hours: float
    priority_score: float


# ---------------------------------------------------------------------------
# Predicted priority topics
# ---------------------------------------------------------------------------

class ModuleTopicPriorityOut(BaseModel):
    subject_name: str
    module_no: int
    topic_name: str
    question_count: int
    weighted_score: float
    priority_label: str
