"""
Data structures and enums for AI Learning integration.
"""

from enum import Enum


class CourseGenerationStatus(str, Enum):
    """Status of course generation process."""
    PENDING = 'pending'
    GENERATING = 'generating'
    COMPLETED = 'completed'
    FAILED = 'failed'


class InteractionType(str, Enum):
    """Types of adaptive interactions."""
    ASSESSMENT = 'assessment'
    TUTOR_CHAT = 'tutor_chat'
    CONTENT_VIEW = 'content_view'
    ADAPTATION = 'adaptation'


class AdaptationType(str, Enum):
    """Types of adaptations the AI Engine can trigger."""
    UNLOCK_CONTENT = 'unlock_content'
    ADD_REMEDIAL = 'add_remedial'
    SKIP_AHEAD = 'skip_ahead'
    TRIGGER_TUTOR = 'trigger_tutor'
    ADJUST_DIFFICULTY = 'adjust_difficulty'
    SUGGEST_REVIEW = 'suggest_review'


class LearningStyle(str, Enum):
    """Identified learning styles."""
    VISUAL = 'visual'
    AUDITORY = 'auditory'
    KINESTHETIC = 'kinesthetic'
    READING_WRITING = 'reading_writing'
    MIXED = 'mixed'
    UNKNOWN = 'unknown'


class QuestionType(str, Enum):
    """Types of assessment questions."""
    MULTIPLE_CHOICE = 'multiple_choice'
    TRUE_FALSE = 'true_false'
    SHORT_ANSWER = 'short_answer'
    ESSAY = 'essay'
    NUMERIC = 'numeric'
    CODE = 'code'
    DRAG_DROP = 'drag_drop'


class DifficultyLevel(str, Enum):
    """Difficulty levels for content and assessments."""
    BEGINNER = 'beginner'
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'
    EXPERT = 'expert'


class WebhookStatus(str, Enum):
    """Status of webhook processing."""
    RECEIVED = 'received'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
