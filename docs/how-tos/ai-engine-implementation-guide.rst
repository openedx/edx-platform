AI Engine Implementation Guide
################################

This guide provides detailed instructions for implementing the AI Engine microservices
that power the adaptive learning system.

Overview
********

The AI Engine is a FastAPI-based microservices application that provides:

1. **Curriculum Generation** - Creates structured course curricula from natural language prompts
2. **Content Creation** - Generates lessons, assessments, and media using LLMs
3. **Student Modeling** - Tracks and analyzes individual learning patterns
4. **Adaptation** - Makes real-time decisions about content delivery and pacing

Technology Stack
****************

Core Framework
==============

* **FastAPI 0.109+** - Web framework
* **Python 3.11+** - Programming language
* **Pydantic 2.0+** - Data validation
* **uvicorn** - ASGI server

Databases
=========

* **PostgreSQL 15+** - Primary data store
* **Redis 7+** - Caching and task queue
* **Qdrant/Pinecone** - Vector database for embeddings

LLM Integration
===============

* **LangChain 0.1+** - LLM orchestration
* **Google Gemini API** - Primary LLM (configurable)
* **Anthropic Claude API** - Alternative LLM
* **OpenAI API** - Alternative LLM

Additional Libraries
====================

* **SQLAlchemy 2.0+** - ORM
* **Alembic** - Database migrations
* **Celery** - Task queue
* **httpx** - Async HTTP client
* **pytest** - Testing
* **prometheus-client** - Metrics

Project Structure
*****************

Create the following directory structure for the AI Engine::

    ai-engine/
    ├── app/
    │   ├── __init__.py
    │   ├── main.py                    # FastAPI application
    │   ├── config.py                  # Configuration
    │   ├── dependencies.py            # FastAPI dependencies
    │   │
    │   ├── api/
    │   │   ├── __init__.py
    │   │   ├── v1/
    │   │   │   ├── __init__.py
    │   │   │   ├── curriculum.py      # Curriculum endpoints
    │   │   │   ├── content.py         # Content generation endpoints
    │   │   │   ├── students.py        # Student profile endpoints
    │   │   │   ├── interactions.py    # Interaction recording endpoints
    │   │   │   ├── adaptation.py      # Adaptation endpoints
    │   │   │   └── tutor.py           # AI tutor endpoints
    │   │
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── curriculum_generator.py
    │   │   ├── content_creator.py
    │   │   ├── student_modeler.py
    │   │   └── adaptation_engine.py
    │   │
    │   ├── llm/
    │   │   ├── __init__.py
    │   │   ├── providers.py           # LLM provider abstractions
    │   │   ├── prompts.py             # Prompt templates
    │   │   └── chains.py              # LangChain workflows
    │   │
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── database.py            # SQLAlchemy models
    │   │   └── schemas.py             # Pydantic schemas
    │   │
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── session.py             # Database session management
    │   │   └── repositories.py        # Data access layer
    │   │
    │   └── utils/
    │       ├── __init__.py
    │       ├── embeddings.py          # Vector embeddings
    │       ├── cache.py               # Caching utilities
    │       └── webhooks.py            # Webhook client for Open edX
    │
    ├── alembic/                       # Database migrations
    │   ├── versions/
    │   └── env.py
    │
    ├── tests/
    │   ├── conftest.py
    │   ├── test_api/
    │   ├── test_services/
    │   └── test_llm/
    │
    ├── scripts/
    │   ├── init_db.py
    │   └── seed_data.py
    │
    ├── docker/
    │   ├── Dockerfile
    │   ├── docker-compose.yml
    │   └── .env.example
    │
    ├── requirements.txt
    ├── requirements-dev.txt
    ├── pyproject.toml
    ├── README.md
    └── .env

Step 1: Initialize Project
***************************

Create project directory and virtual environment::

    mkdir ai-engine
    cd ai-engine
    python3.11 -m venv venv
    source venv/bin/activate  # On Windows: venv\\Scripts\\activate

Create ``requirements.txt``::

    fastapi==0.109.0
    uvicorn[standard]==0.27.0
    pydantic==2.5.0
    pydantic-settings==2.1.0
    sqlalchemy==2.0.25
    alembic==1.13.1
    psycopg2-binary==2.9.9
    redis==5.0.1
    langchain==0.1.0
    langchain-google-genai==0.0.6
    langchain-anthropic==0.0.1
    openai==1.10.0
    httpx==0.26.0
    celery==5.3.6
    qdrant-client==1.7.0
    prometheus-fastapi-instrumentator==6.1.0
    python-jose[cryptography]==3.3.0
    passlib[bcrypt]==1.7.4
    pytest==7.4.4
    pytest-asyncio==0.23.3

Install dependencies::

    pip install -r requirements.txt

Step 2: Configuration
**********************

Create ``app/config.py``::

    from pydantic_settings import BaseSettings
    from functools import lru_cache

    class Settings(BaseSettings):
        # Application
        APP_NAME: str = "AI Learning Engine"
        APP_VERSION: str = "1.0.0"
        API_V1_PREFIX: str = "/api/v1"
        DEBUG: bool = False

        # Server
        HOST: str = "0.0.0.0"
        PORT: int = 8001

        # Security
        SECRET_KEY: str
        API_KEY_NAME: str = "X-API-Key"
        ALLOWED_HOSTS: list[str] = ["*"]

        # Database
        DATABASE_URL: str
        DB_POOL_SIZE: int = 20
        DB_MAX_OVERFLOW: int = 40

        # Redis
        REDIS_URL: str
        REDIS_CACHE_TTL: int = 300

        # LLM Provider
        LLM_PROVIDER: str = "gemini"  # gemini, claude, openai
        LLM_MODEL: str = "gemini-2.0-flash-exp"
        LLM_TEMPERATURE: float = 0.7
        LLM_MAX_TOKENS: int = 2048

        # API Keys
        GOOGLE_API_KEY: str = ""
        ANTHROPIC_API_KEY: str = ""
        OPENAI_API_KEY: str = ""

        # Vector Database
        VECTOR_DB_URL: str = ""
        VECTOR_DB_COLLECTION: str = "learning_content"

        # Open edX Integration
        OPENEDX_BASE_URL: str
        OPENEDX_API_KEY: str
        OPENEDX_WEBHOOK_SECRET: str

        # Celery
        CELERY_BROKER_URL: str
        CELERY_RESULT_BACKEND: str

        class Config:
            env_file = ".env"
            case_sensitive = True

    @lru_cache()
    def get_settings() -> Settings:
        return Settings()

Create ``.env.example``::

    # Application
    APP_NAME="AI Learning Engine"
    DEBUG=false

    # Security
    SECRET_KEY=your-secret-key-here
    API_KEY_NAME=X-API-Key

    # Database
    DATABASE_URL=postgresql://user:password@localhost:5432/ai_engine
    DB_POOL_SIZE=20

    # Redis
    REDIS_URL=redis://localhost:6379/0
    REDIS_CACHE_TTL=300

    # LLM Configuration
    LLM_PROVIDER=gemini
    LLM_MODEL=gemini-2.0-flash-exp
    LLM_TEMPERATURE=0.7
    LLM_MAX_TOKENS=2048

    # API Keys
    GOOGLE_API_KEY=your-google-api-key
    ANTHROPIC_API_KEY=your-anthropic-api-key
    OPENAI_API_KEY=your-openai-api-key

    # Vector Database (Qdrant)
    VECTOR_DB_URL=http://localhost:6333
    VECTOR_DB_COLLECTION=learning_content

    # Open edX Integration
    OPENEDX_BASE_URL=https://your-openedx-instance.org
    OPENEDX_API_KEY=your-openedx-api-key
    OPENEDX_WEBHOOK_SECRET=your-webhook-secret

    # Celery
    CELERY_BROKER_URL=redis://localhost:6379/1
    CELERY_RESULT_BACKEND=redis://localhost:6379/2

Step 3: Database Models
************************

Create ``app/models/database.py``::

    from datetime import datetime
    from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Float, Boolean, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship

    Base = declarative_base()

    class Course(Base):
        __tablename__ = "courses"

        id = Column(Integer, primary_key=True, index=True)
        course_key = Column(String(255), unique=True, index=True)
        title = Column(String(255))
        description = Column(Text)
        generation_prompt = Column(Text)
        status = Column(String(50), default="generating")
        curriculum_data = Column(JSON)
        metadata = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        modules = relationship("Module", back_populates="course")

    class Module(Base):
        __tablename__ = "modules"

        id = Column(Integer, primary_key=True, index=True)
        course_id = Column(Integer, ForeignKey("courses.id"))
        module_id = Column(String(100), index=True)
        title = Column(String(255))
        description = Column(Text)
        order = Column(Integer)
        metadata = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)

        course = relationship("Course", back_populates="modules")
        lessons = relationship("Lesson", back_populates="module")

    class Lesson(Base):
        __tablename__ = "lessons"

        id = Column(Integer, primary_key=True, index=True)
        module_id = Column(Integer, ForeignKey("modules.id"))
        lesson_id = Column(String(100), index=True)
        title = Column(String(255))
        content = Column(Text)
        content_type = Column(String(50))
        difficulty = Column(String(20))
        order = Column(Integer)
        metadata = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)

        module = relationship("Module", back_populates="lessons")

    class StudentProfile(Base):
        __tablename__ = "student_profiles"

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, unique=True, index=True)
        username = Column(String(150))
        learning_style = Column(String(50))
        mastered_concepts = Column(JSON, default=list)
        struggling_concepts = Column(JSON, default=list)
        preferences = Column(JSON, default=dict)
        performance_metrics = Column(JSON, default=dict)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        interactions = relationship("Interaction", back_populates="student")

    class Interaction(Base):
        __tablename__ = "interactions"

        id = Column(Integer, primary_key=True, index=True)
        student_id = Column(Integer, ForeignKey("student_profiles.id"))
        course_key = Column(String(255), index=True)
        usage_key = Column(String(255))
        interaction_type = Column(String(50), index=True)
        interaction_data = Column(JSON)
        ai_response = Column(JSON)
        response_time_ms = Column(Integer)
        created_at = Column(DateTime, default=datetime.utcnow)

        student = relationship("StudentProfile", back_populates="interactions")

Step 4: Main Application
*************************

Create ``app/main.py``::

    from fastapi import FastAPI, Depends, HTTPException, Security
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security.api_key import APIKeyHeader
    from prometheus_fastapi_instrumentator import Instrumentator

    from app.config import get_settings
    from app.api.v1 import curriculum, content, students, interactions, adaptation, tutor

    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus metrics
    Instrumentator().instrument(app).expose(app)

    # Include routers
    app.include_router(
        curriculum.router,
        prefix=f"{settings.API_V1_PREFIX}/curriculum",
        tags=["curriculum"]
    )
    app.include_router(
        content.router,
        prefix=f"{settings.API_V1_PREFIX}/content",
        tags=["content"]
    )
    app.include_router(
        students.router,
        prefix=f"{settings.API_V1_PREFIX}/students",
        tags=["students"]
    )
    app.include_router(
        interactions.router,
        prefix=f"{settings.API_V1_PREFIX}/interactions",
        tags=["interactions"]
    )
    app.include_router(
        adaptation.router,
        prefix=f"{settings.API_V1_PREFIX}/adaptation",
        tags=["adaptation"]
    )
    app.include_router(
        tutor.router,
        prefix=f"{settings.API_V1_PREFIX}/tutor",
        tags=["tutor"]
    )

    @app.get("/")
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running"
        }

    @app.get("/api/v1/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }

    if __name__ == "__main__":
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG
        )

Step 5: Implement Services
***************************

The four core microservices need to be implemented:

Curriculum Generator Service
=============================

Location: ``app/services/curriculum_generator.py``

This service generates structured course curricula from natural language prompts.

Key responsibilities:

* Parse course generation prompts
* Use LLM to generate course outline
* Structure curriculum into modules and lessons
* Define learning objectives and prerequisites
* Estimate time requirements

Content Creator Service
=======================

Location: ``app/services/content_creator.py``

This service generates actual lesson content, assessments, and media.

Key responsibilities:

* Generate lesson text with examples
* Create assessment questions of various types
* Generate code examples and exercises
* Create diagrams and visualizations (via image generation APIs)
* Ensure content aligns with curriculum objectives

Student Modeler Service
========================

Location: ``app/services/student_modeler.py``

This service maintains and analyzes student learning profiles.

Key responsibilities:

* Track student progress and performance
* Identify learning patterns and styles
* Maintain lists of mastered/struggling concepts
* Calculate performance metrics
* Predict future performance

Adaptation Engine Service
==========================

Location: ``app/services/adaptation_engine.py``

This service makes decisions about content adaptation.

Key responsibilities:

* Analyze student performance data
* Determine appropriate difficulty adjustments
* Decide when to provide remedial content
* Trigger AI tutor interventions
* Coordinate with other services

Step 6: LLM Integration
************************

Create ``app/llm/providers.py`` to abstract LLM provider interactions::

    from abc import ABC, abstractmethod
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_anthropic import ChatAnthropic
    from langchain_openai import ChatOpenAI
    from app.config import get_settings

    class LLMProvider(ABC):
        @abstractmethod
        async def generate(self, prompt: str, **kwargs) -> str:
            pass

    class GeminiProvider(LLMProvider):
        def __init__(self):
            settings = get_settings()
            self.llm = ChatGoogleGenerativeAI(
                model=settings.LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=settings.LLM_TEMPERATURE
            )

        async def generate(self, prompt: str, **kwargs) -> str:
            response = await self.llm.ainvoke(prompt)
            return response.content

    # Similar implementations for Claude and OpenAI...

Create ``app/llm/prompts.py`` with prompt templates::

    CURRICULUM_GENERATION_PROMPT = """
    You are an expert curriculum designer. Generate a comprehensive curriculum for the following course:

    Course Request: {course_prompt}

    Create a structured curriculum with:
    1. Course title and description
    2. Learning objectives
    3. Modules (major topics)
    4. Lessons within each module
    5. Estimated time for each component

    Return the curriculum in JSON format.
    """

    LESSON_CONTENT_PROMPT = """
    Create engaging lesson content for:

    Course: {course_title}
    Module: {module_title}
    Lesson: {lesson_title}
    Learning Objectives: {objectives}

    Include:
    - Clear explanations with examples
    - Visual descriptions where helpful
    - Practice problems
    - Real-world applications

    Target audience level: {difficulty_level}
    """

    # More prompts for different use cases...

Step 7: API Endpoints
*********************

Implement API endpoints for each service. Example for curriculum generation
in ``app/api/v1/curriculum.py``::

    from fastapi import APIRouter, Depends, HTTPException
    from sqlalchemy.orm import Session
    from app.services.curriculum_generator import CurriculumGeneratorService
    from app.models.schemas import CourseGenerationRequest, CourseResponse
    from app.db.session import get_db

    router = APIRouter()

    @router.post("/generate", response_model=CourseResponse)
    async def generate_curriculum(
        request: CourseGenerationRequest,
        db: Session = Depends(get_db)
    ):
        """Generate a new course curriculum from a prompt."""
        service = CurriculumGeneratorService(db)
        course = await service.generate_curriculum(
            prompt=request.prompt,
            course_key=request.course_key,
            user_id=request.user_id,
            metadata=request.metadata
        )
        return course

    # More endpoints...

Step 8: Testing
***************

Create comprehensive tests in the ``tests/`` directory::

    # tests/conftest.py
    import pytest
    from fastapi.testclient import TestClient
    from app.main import app

    @pytest.fixture
    def client():
        return TestClient(app)

    @pytest.fixture
    def mock_llm():
        # Mock LLM for testing
        pass

Run tests::

    pytest tests/ -v --cov=app

Step 9: Docker Deployment
**************************

Create ``docker/Dockerfile``::

    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY app/ ./app/
    COPY alembic/ ./alembic/
    COPY alembic.ini .

    EXPOSE 8001

    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

Create ``docker/docker-compose.yml``::

    version: '3.8'

    services:
      ai-engine:
        build:
          context: ..
          dockerfile: docker/Dockerfile
        ports:
          - "8001:8001"
        environment:
          - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_engine
          - REDIS_URL=redis://redis:6379/0
        depends_on:
          - postgres
          - redis
          - qdrant

      postgres:
        image: postgres:15
        environment:
          POSTGRES_DB: ai_engine
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        volumes:
          - postgres_data:/var/lib/postgresql/data

      redis:
        image: redis:7
        volumes:
          - redis_data:/data

      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - "6333:6333"
        volumes:
          - qdrant_data:/qdrant/storage

    volumes:
      postgres_data:
      redis_data:
      qdrant_data:

Step 10: Running the Application
*********************************

1. Copy ``.env.example`` to ``.env`` and fill in your API keys and configuration
2. Start services::

    docker-compose -f docker/docker-compose.yml up -d

3. Run migrations::

    alembic upgrade head

4. Start the application::

    uvicorn app.main:app --reload

5. Access API documentation at http://localhost:8001/docs

Next Steps
**********

1. Implement each microservice with full business logic
2. Add comprehensive error handling and logging
3. Implement rate limiting and authentication
4. Set up monitoring and alerting
5. Add comprehensive unit and integration tests
6. Document all API endpoints
7. Create deployment guides for production

For more information, see:

* ADR 0024: AI-Powered Adaptive Learning Engine
* Open edX Integration Documentation
* LangChain Documentation: https://python.langchain.com/
* FastAPI Documentation: https://fastapi.tiangolo.com/
