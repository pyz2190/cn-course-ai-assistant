from enum import StrEnum


class Language(StrEnum):
    ZH = "zh"
    EN = "en"
    BILINGUAL = "bilingual"


class ContentType(StrEnum):
    PDF = "pdf"
    PPT = "ppt"
    SUBTITLE = "subtitle"
    TEXT = "text"
    RFC = "rfc"
    TABLE = "table"
    FORMULA = "formula"
    IMAGE = "image"
    DIAGRAM = "diagram"
    OTHER = "other"


class ResourceType(StrEnum):
    TEXTBOOK = "textbook"
    SLIDE = "slide"
    LAB_GUIDE = "lab_guide"
    VIDEO_SUBTITLE = "video_subtitle"
    RFC = "rfc"
    OTHER = "other"


class AccessLevel(StrEnum):
    PUBLIC = "public"
    COURSE = "course"
    PRIVATE = "private"


class ParseStatus(StrEnum):
    PENDING = "pending"
    PARSED = "parsed"
    FAILED = "failed"


class SyncStatus(StrEnum):
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed"


class Difficulty(StrEnum):
    INTRODUCTORY = "introductory"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    REVIEWED = "reviewed"
    APPROVED = "approved"


class EvaluationReviewStatus(StrEnum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISED = "revised"


class TaskType(StrEnum):
    FOUNDATION = "foundation"
    PROTOCOL_ANALYSIS = "protocol_analysis"
    CASE_STUDY = "case_study"
    INNOVATION_CHALLENGE = "innovation_challenge"
    PROJECT_PRACTICE = "project_practice"
    TROUBLESHOOTING = "troubleshooting"


class ExerciseType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ANALYSIS = "analysis"
    DESIGN = "design"


class ExerciseSource(StrEnum):
    TEXTBOOK = "textbook"
    LAB_GUIDE = "lab_guide"
    PAST_EXAM = "past_exam"
    COURSE_TEAM = "course_team"


class TaskStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"


class QuestionCategory(StrEnum):
    CONCEPT = "concept"
    PROTOCOL_DETAIL = "protocol_detail"
    TOOL_TUTORIAL = "tool_tutorial"
    LAB = "lab"
    COMMON_ERROR = "common_error"
    REVIEW = "review"


class ScoringDimension(StrEnum):
    CORRECTNESS = "correctness"
    CITATION_ACCURACY = "citation_accuracy"
    HALLUCINATION_RATE = "hallucination_rate"


class EventType(StrEnum):
    QA_ASKED = "qa_asked"
    TASK_OPENED = "task_opened"
    TASK_COMPLETED = "task_completed"
    FEEDBACK_SUBMITTED = "feedback_submitted"


class FeedbackStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class KnowledgeBaseChangeStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    WONT_FIX = "wont_fix"
