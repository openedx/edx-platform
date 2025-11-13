# Open edX Platform - AI Assistant Guide

This document provides a comprehensive guide for AI assistants working with the Open edX Platform codebase. It covers the structure, conventions, workflows, and best practices essential for effective code development and maintenance.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Codebase Structure](#codebase-structure)
4. [Architectural Patterns](#architectural-patterns)
5. [Development Workflows](#development-workflows)
6. [Testing Conventions](#testing-conventions)
7. [Code Quality Standards](#code-quality-standards)
8. [Common Operations](#common-operations)
9. [Key Conventions](#key-conventions)
10. [Important References](#important-references)

---

## Project Overview

**Open edX Platform** is an enterprise-grade, open-source learning management system (LMS) that powers online education at scale.

### Core Components

- **LMS (Learning Management System)**: `/lms/` - Delivers learning content to students
- **CMS (Content Management Service)**: `/cms/` - Studio for authoring course content
- **XModule**: `/xmodule/` - XBlock implementations for course content blocks
- **Common**: `/common/` - Shared code between LMS and CMS
- **OpenEdx**: `/openedx/` - Modern feature-oriented organization

### Key Characteristics

- **License**: AGPL v3
- **Architecture**: Modular monolith with pluggable components
- **Languages**: Python 3.11, JavaScript/JSX, SCSS
- **Frameworks**: Django, React, RequireJS
- **Databases**: MySQL 8.0, MongoDB 7.x, Memcached, Redis

---

## Technology Stack

### Backend

- **Python 3.11** with Django framework
- **Celery 5.5.3** for asynchronous task processing
- **Django REST Framework** for API endpoints
- **MySQL 8.0**: Primary relational database for user data, enrollments, grades
- **MongoDB 7.x**: Course structure and content storage (modulestore)
- **Redis/Memcached**: Caching and session storage
- **Elasticsearch/Meilisearch**: Full-text search (optional)

### Frontend

- **JavaScript (ES6+)** with Babel transpilation
- **React 16.14** (gradually being modernized)
- **Redux 3.7.2** for state management
- **RequireJS 2.3.7** and **Webpack 5.90.3** for module loading
- **Paragon 2.6.4**: edX design system
- **Bootstrap 4.0.0** and **jQuery 2.2.4** (legacy)
- **Sass 1.54.8** for CSS preprocessing

### Key Python Dependencies

```
# Authentication & Authorization
openedx-authz
oauth2-provider
django-cors-headers

# Content & Learning
xblock
edx-opaque-keys
lti-consumer-xblock
ora2 (Open Response Assessment)
edx-proctoring

# Data & APIs
djangorestframework
pydantic
sqlalchemy

# Enterprise & Features
edx-enterprise
edx-ace (email/notifications)

# Infrastructure
celery
boto3 (AWS S3)
pymongo
requests
pillow
bleach
```

### Testing Tools

- **Python**: pytest, pytest-django, coverage.py, mypy, pylint
- **JavaScript**: Jest 29.7.0, Karma 0.13.22, Jasmine, Sinon

---

## Codebase Structure

```
/home/user/enchanted_edx/
├── cms/                          # Content Management System (Studio)
│   ├── djangoapps/              # 11 CMS-specific Django apps
│   │   ├── contentstore/        # Main content editing functionality
│   │   ├── api/                 # REST APIs for content operations
│   │   ├── course_creators/     # Course creation workflows
│   │   ├── models/              # CMS-specific models
│   │   └── xblock_config/       # XBlock configuration
│   ├── envs/                    # Environment configurations
│   ├── static/                  # CMS static assets
│   ├── templates/               # CMS HTML templates
│   └── urls.py                  # CMS URL routing
│
├── lms/                          # Learning Management System
│   ├── djangoapps/              # 46+ LMS-specific Django apps
│   │   ├── courseware/          # Core course delivery
│   │   ├── grades/              # Grading engine
│   │   ├── course_api/          # Course data APIs
│   │   ├── discussion/          # Discussion forums
│   │   ├── certificates/        # Certificate generation
│   │   ├── instructor/          # Instructor tools
│   │   ├── teams/               # Team collaboration
│   │   └── ...                  # Many more apps
│   ├── envs/                    # Environment configurations
│   ├── static/                  # LMS static assets
│   ├── templates/               # LMS HTML templates
│   └── urls.py                  # LMS URL routing
│
├── common/                       # Shared code (LMS + CMS)
│   ├── djangoapps/              # 16 shared Django apps
│   │   ├── student/             # User/enrollment management
│   │   ├── track/               # Event tracking/analytics
│   │   ├── course_modes/        # Enrollment modes (audit, verified)
│   │   ├── third_party_auth/    # OAuth/SAML integrations
│   │   └── ...
│   ├── static/                  # Common static assets
│   ├── templates/               # Common templates
│   └── test/                    # Common test utilities
│
├── openedx/                      # Modern feature-oriented organization
│   ├── core/                    # Core infrastructure (69 djangoapps)
│   │   ├── djangoapps/          # Core services
│   │   │   ├── agreements/
│   │   │   ├── bookmarks/
│   │   │   ├── content_libraries/
│   │   │   ├── discussions/
│   │   │   ├── course_live/
│   │   │   ├── credentials/
│   │   │   ├── user_authn/
│   │   │   └── ...
│   │   └── lib/                 # Core utilities
│   └── features/                # Feature modules (16 features)
│       ├── calendar_sync/
│       ├── content_type_gating/
│       ├── course_experience/
│       ├── discounts/
│       └── enterprise_support/
│
├── xmodule/                      # XBlock implementations (30+ types)
│   ├── capa_block.py            # Problem/Assessment blocks
│   ├── video_block.py           # Video player
│   ├── html_block.py            # HTML content
│   ├── discussion_block.py      # Discussion forums
│   ├── seq_block.py             # Sequences (chapters/sections)
│   ├── course_block.py          # Course container
│   ├── library_content_block.py # Content library references
│   ├── lti_block.py             # LTI integration
│   ├── modulestore/             # Content storage abstraction
│   ├── capa/                    # Problem engine
│   └── js/                      # JavaScript implementations
│
├── docs/                         # Documentation and ADRs
├── requirements/                 # Python dependencies
│   ├── edx/                     # Main requirements
│   │   ├── base.txt             # Production
│   │   ├── development.txt      # Development
│   │   ├── testing.txt          # Testing
│   │   └── assets.txt           # Asset building
│   └── constraints.txt          # Version constraints
│
├── scripts/                      # Build and utility scripts
├── webpack-config/              # Webpack configuration modules
├── themes/                       # Theming system
├── test_root/                    # Test infrastructure
├── conf/                         # Configuration templates
│
├── manage.py                     # Django management (use: ./manage.py lms|cms)
├── setup.py                      # Package definition, XBlock entry points
├── package.json                  # npm dependencies and scripts
├── Makefile                      # Development tasks
└── webpack.*.config.js          # Webpack build configurations
```

---

## Architectural Patterns

### 1. Modular Monolith

The codebase is a **modular monolith** with strict boundaries:

- **LMS and CMS are independent**: They cannot import from each other
- **Shared code lives in common/ and openedx/**
- **Import linting enforces boundaries** via `setup.cfg` (lines 68-182)
- Each service runs independently: `./manage.py lms` or `./manage.py cms`

### 2. XBlock Pluggable Architecture

**XBlocks** are pluggable content blocks that extend the platform:

- Content is organized as pluggable "blocks" (video, problem, discussion, HTML)
- Each XBlock implements standard interfaces: `render()`, `serialize()`, `get_data()`
- **30+ built-in XBlock types** defined in `setup.py` entry points
- Located in `/xmodule/` with implementations for each block type

**Common XBlock Types:**
```python
"problem"      → xmodule.capa_block:ProblemBlock       # Assessments
"video"        → xmodule.video_block:VideoBlock        # Video player
"html"         → xmodule.html_block:HtmlBlock          # HTML content
"discussion"   → xmodule.discussion_block:DiscussionXBlock
"sequential"   → xmodule.seq_block:SequenceBlock       # Chapters
"vertical"     → xmodule.vertical_block:VerticalBlock  # Sections
"course"       → xmodule.course_block:CourseBlock      # Course container
"library"      → xmodule.library_root_xblock:LibraryRoot
```

### 3. Inter-App API Pattern (OEP-49)

**CRITICAL**: Apps must communicate through explicit APIs only.

**Rules** (from `/docs/decisions/0002-inter-app-apis.rst`):

1. Each Django app exposes APIs via `api.py` in the app's root directory
2. APIs should be domain-relevant, well-named, and self-consistent
3. **NEVER expose Django models directly** via APIs
4. Test-only APIs go in `api_for_tests.py`
5. Import linter enforces API-only access between apps

**Example**: `/lms/djangoapps/grades/api.py` - Grade-related public functions

**Why This Matters**:
- Prevents tight coupling between apps
- Enables safe refactoring within apps
- Makes dependencies explicit and trackable

### 4. Django App Organization

The platform organizes functionality into focused Django apps:

**LMS Apps (46+)**:
- `courseware` - Course delivery engine
- `grades` - Grading calculations and persistence
- `certificates` - Certificate generation and management
- `instructor` - Instructor dashboard and tools
- `discussion` - Forum integration
- `teams` - Collaborative learning teams

**CMS Apps (11)**:
- `contentstore` - Primary content editing
- `api` - REST APIs for Studio
- `course_creators` - Course creation workflows

**Common Apps (16)**:
- `student` - User accounts and enrollments
- `track` - Event tracking for analytics
- `course_modes` - Audit, verified, professional modes
- `third_party_auth` - OAuth, SAML, SSO

### 5. Event-Driven Architecture

Uses **openedx-events** for cross-app communication:

- Apps emit domain events on significant actions
- Other apps subscribe without direct coupling
- Examples: course publication, enrollment changes, grade updates
- Enables async processing via Celery tasks

### 6. Feature Flags System

Heavy use of feature flags for gradual rollouts:

- Feature flags stored in `FEATURES` dictionary in settings
- Runtime evaluation of feature availability
- Allows toggle without code deployment
- Location: `/openedx/features/` - Feature modules with toggles

### 7. Multi-Database Strategy

Different data stores optimized for specific purposes:

- **MySQL**: Student data, enrollments, grades, user profiles, course metadata
- **MongoDB**: Course structure, content XML, student state (modulestore)
- **Redis/Memcached**: Caching, sessions, rate limiting
- **Elasticsearch**: Full-text search (optional)

### 8. Micro-Frontends (MFE) Integration

Modern frontends are separate React applications:

- **MFEs run on separate ports** and communicate via REST APIs
- Legacy Django templates being gradually replaced
- Configuration via settings: `*_MICROFRONTEND_URL`

**Expected MFEs** (with default ports):
- `frontend-app-authoring` → localhost:2001
- `frontend-app-learning` → localhost:2000
- `frontend-app-learner-dashboard` → localhost:1996
- `frontend-app-profile` → localhost:1995
- `frontend-app-account` → localhost:1997

### 9. Content Transformation Pipeline

**Block Transformers** modify course structure based on context:

Defined in `setup.py` entry points (lines 113-131):
- `library_content` - Resolve library references
- `split_test` - Apply A/B test variations
- `user_partitions` - Apply cohort/track visibility rules
- `grades` - Compute grade metadata

### 10. Settings Hierarchy

Environment-specific configuration with inheritance:

```
common.py (base settings)
  ├── test.py (testing overrides)
  ├── production.py (production settings)
  └── development.py (development overrides)
```

**Configuration Sources**:
1. Defaults in `common.py`
2. Environment variables
3. YAML config files (production)
4. Django admin editable settings (ConfigModel)

---

## Development Workflows

### Environment Setup

**System Requirements**:
- Ubuntu 24.04
- Python 3.11
- Node.js (see `.nvmrc`)
- MySQL 8.0
- MongoDB 7.x
- Memcached

**Install Dependencies**:
```bash
# Python requirements
make requirements              # Installs development requirements
# OR
pip install -r requirements/edx/development.txt
pip install -e .

# JavaScript requirements
npm clean-install --dev        # Development mode
# OR
npm clean-install              # Production mode
```

### Database Setup

```bash
# Run migrations for both services
./manage.py lms migrate
./manage.py lms migrate --database=student_module_history
./manage.py cms migrate
```

### Building Assets

```bash
# Development build (faster, with source maps)
npm run build-dev

# Production build (optimized)
npm run build

# Watch mode (auto-rebuild on changes)
npm run watch

# Individual tasks
npm run webpack        # JavaScript bundling
npm run compile-sass   # SCSS to CSS
```

### Running the Platform

**Start Services**:
```bash
# Start LMS (Learning Management System)
./manage.py lms runserver 18000

# Start CMS (Studio)
./manage.py cms runserver 18010
```

**Note**: Most UI functionality requires running MFEs separately.

### Translations

```bash
# Extract translatable strings
make extract_translations

# Pull translations from Atlas
make pull_translations

# Compile translations
./manage.py lms compilemessages
./manage.py lms compilejsi18n
./manage.py cms compilejsi18n
```

### Common Make Commands

```bash
make help                      # Show all available targets
make requirements             # Install development requirements
make clean                    # Clean git-ignored files
make docs                     # Build documentation
make pull_translations        # Pull and compile translations
make migrate                  # Run migrations for both LMS and CMS
```

---

## Testing Conventions

### Test Philosophy

Follow the **test pyramid**: Heavy investment in unit tests, moderate integration tests.

- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test multiple units working together
- **Mock external dependencies**: Use `unittest.mock` for external services

### Test Organization

**Python Tests**:
- Located in `tests/` subdirectories within each app
- Example: `/xmodule/capa/tests/`, `/lms/djangoapps/grades/tests/`
- Use `test_*.py` or `*_tests.py` naming convention

**JavaScript Tests**:
- Located in `spec/` subdirectories
- Example: `/lms/static/js/spec/`, `/xmodule/js/spec/`
- Mirror source directory structure
- Use `*_spec.js` naming convention

### Running Python Tests

**Using pytest** (recommended):

```bash
# Run all tests in a module
pytest path/test_module.py

# Run a specific test function
pytest path/test_module.py::test_func

# Run all tests in a class
pytest path/test_module.py::TestClass

# Run a specific test method
pytest path/test_module.py::TestClass::test_method

# Run all tests in a directory
pytest path/testing/

# Run with specific Django settings
pytest test --ds=lms.envs.test
pytest test --ds=cms.envs.test

# Run with specific root directory
pytest test --rootdir lms
pytest test --rootdir cms

# Filter tests by name pattern
pytest path/test_module.py -k test_pattern

# Run with coverage
pytest path/test_module.py --cov --cov-config=.coveragerc-local

# Debug with pdb
pytest path/test_module.py --pdb

# Stop on first failure
pytest path/test_module.py --exitfirst
```

**Test Database Options**:
- `--reuse-db`: Persist database between runs (default, faster)
- `--create-db --migrations`: Test against migrated database (slower)

### Running JavaScript Tests

```bash
# Run all tests (Karma + Jest)
npm run test

# Run only Karma (Jasmine) tests
npm run test-karma

# Run only Jest tests
npm run test-jest

# Run tests by service
npm run test-lms
npm run test-cms
npm run test-xmodule
npm run test-common

# Run specific Karma test types
npm run test-karma-vanilla  # Legacy JS (no RequireJS)
npm run test-karma-require  # JS with RequireJS
npm run test-karma-webpack  # JS built with Webpack (currently broken)
```

### Test Factories

Use **Factory Boy** for test data creation:

- Factories encapsulate object creation logic
- Located near the code they test
- Example: `/xmodule/capa/tests/response_xml_factory.py`
- Reduces test setup boilerplate
- Ensures consistent test data

### Coverage Analysis

```bash
# Run tests with coverage
pytest cms/djangoapps/contentstore/tests/test_import.py \
    --cov \
    --cov-config=.coveragerc-local

# Generate coverage report for specific file
pytest lms/djangoapps/grades/tests/test_subsection_grade.py \
    --cov=lms.djangoapps.grades.subsection_grade \
    --cov-config=.coveragerc-local \
    --cov-report=term-missing

# Generate HTML coverage report
coverage html
# View at: reports/xmodule/cover/index.html
```

**Important**: Always use `--cov-config=.coveragerc-local` for local development.

### Testing Best Practices

1. **Prefer unit tests over integration tests** for better maintainability
2. **Mock external dependencies**: APIs, email, file I/O, third-party services
3. **Use factories for model creation** instead of manual instantiation
4. **Test both LMS and CMS environments** for common/xmodule code
5. **Focus on testing behavior**, not implementation details
6. **Aim for high branch coverage**, not just line coverage
7. **Keep tests fast**: Mock slow operations, use `--reuse-db`
8. **Use descriptive test names** that explain what is being tested

---

## Code Quality Standards

### Quality Checks

Run these before committing code:

```bash
# Python type checking
mypy path/to/code

# Python style checking
pycodestyle path/to/code

# Python linting
pylint path/to/code

# Import boundary enforcement
lint-imports

# Verify __init__.py files
scripts/verify-dunder-init.sh

# XSS vulnerability checking
make xsslint

# PII annotation checking
make pii_check

# Reserved keyword checking
make check_keywords
```

### CI/CD Workflows

GitHub Actions workflows (`.github/workflows/`):
- `unit-tests.yml` - Python unit tests
- `js-tests.yml` - JavaScript tests
- `quality-checks.yml` - Code quality (pycodestyle, pylint, mypy)
- `pylint-checks.yml` - Comprehensive pylint checks
- `lint-imports.yml` - Import boundary enforcement
- `migrations-check.yml` - Migration compatibility checks
- `ci-static-analysis.yml` - Static analysis tools

### Code Style Guidelines

**Python**:
- Follow PEP 8 style guide
- Use type hints where beneficial
- Maximum line length: 120 characters (see `setup.cfg`)
- Use `pylintrc` for linting rules

**JavaScript**:
- Follow edX JavaScript style guide
- Use ESLint for linting (gradually being migrated)
- Prefer modern ES6+ syntax for new code
- Use semicolons consistently

### Import Rules

**Critical**: Import linter enforces strict boundaries:

1. **LMS cannot import from CMS** (and vice versa)
2. **Apps should import from other apps' api.py only**
3. **Common and xmodule can be imported by both LMS and CMS**
4. **OpenEdx core can be imported by all**

Violations will fail CI. See `setup.cfg` lines 68-182 for full contract definitions.

### Security Best Practices

1. **NEVER expose secrets** in code (use environment variables)
2. **Sanitize HTML content** using `bleach` library
3. **Validate and escape user input** in all contexts
4. **Use parameterized queries** to prevent SQL injection
5. **Follow OWASP Top 10** security practices
6. **Run security checks**: `make pii_check`, semgrep workflows

---

## Common Operations

### Creating a New Django App

1. **Decide on location** (lms/, cms/, common/, openedx/)
2. **Create app**: `./manage.py lms startapp myapp`
3. **Add to INSTALLED_APPS** in appropriate envs/common.py
4. **Create api.py** for public interfaces
5. **Add tests/** directory with test files
6. **Update import linter rules** in setup.cfg if needed

### Adding a New XBlock Type

1. **Create block class** in `/xmodule/` (e.g., `my_block.py`)
2. **Inherit from XBlock or XModule**
3. **Implement required methods**: `student_view()`, `studio_view()`
4. **Register in setup.py** entry_points under `xblock.v1`
5. **Add JavaScript** in `/xmodule/js/` if needed
6. **Add tests** in `/xmodule/tests/`

### Adding a New REST API

1. **Create views** in app's `views.py` or `api/v1/views.py`
2. **Use Django REST Framework** serializers and viewsets
3. **Add URL patterns** in app's `urls.py`
4. **Include in main urls.py** (`lms/urls.py` or `cms/urls.py`)
5. **Add authentication/permissions** checks
6. **Write tests** for API endpoints
7. **Document API** with docstrings (for Swagger generation)

### Updating Dependencies

**Python dependencies**:
```bash
# Edit requirements/*.in files
# Then compile:
make compile-requirements

# Install updated requirements:
make requirements
```

**JavaScript dependencies**:
```bash
# Update package.json
npm install <package>@<version>

# Rebuild assets
npm run build-dev
```

### Creating Migrations

```bash
# Create migrations for LMS
./manage.py lms makemigrations

# Create migrations for CMS
./manage.py cms makemigrations

# Create migrations for specific app
./manage.py lms makemigrations myapp

# Run migrations
make migrate
```

### Working with Translations

```bash
# Extract new translatable strings
make extract_translations

# Pull latest translations
make pull_translations

# Test with specific language
# Set LANGUAGE_CODE in settings or use Django's i18n middleware
```

### Debugging

**Python debugging**:
```python
# Add breakpoint in code
breakpoint()  # Python 3.7+

# Or use pdb
import pdb; pdb.set_trace()

# Run tests with pdb
pytest path/test.py --pdb
```

**JavaScript debugging**:
- Use browser DevTools
- Add `debugger;` statements in code
- Use source maps for webpack bundles

---

## Key Conventions

### Naming Conventions

**Python**:
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

**JavaScript**:
- Classes: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- React components: `PascalCase`

**Django apps**:
- App names: `lowercase_with_underscores`
- Models: `PascalCase`
- URL names: `app_name:view_name`

### File Organization

**Python modules**:
```
myapp/
├── __init__.py
├── api.py              # Public API (required)
├── api_for_tests.py    # Test-only API (optional)
├── models.py           # Django models
├── views.py            # Django views
├── urls.py             # URL routing
├── serializers.py      # DRF serializers
├── tasks.py            # Celery tasks
├── helpers.py          # Internal helpers
└── tests/              # Test directory
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── factories.py    # Factory Boy factories
```

**JavaScript modules**:
```
static/js/
├── myfeature/
│   ├── models/
│   ├── views/
│   ├── collections/
│   └── spec/          # Tests mirror structure
│       ├── models/
│       └── views/
```

### Import Organization

**Python import order** (enforced by isort):
1. Standard library imports
2. Third-party imports
3. Django imports
4. Local application imports

```python
# Standard library
import os
from datetime import datetime

# Third-party
import requests
from celery import task

# Django
from django.conf import settings
from django.contrib.auth.models import User

# Local
from lms.djangoapps.grades.api import get_grade
from openedx.core.lib.api.authentication import OAuth2Authentication
```

### Django Model Conventions

```python
from django.db import models
from model_utils.models import TimeStampedModel

class MyModel(TimeStampedModel):
    """
    Brief description of the model.

    .. no_pii:
    """
    # Fields in logical order
    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'myapp'
        ordering = ['name']
        verbose_name = 'My Model'
        verbose_name_plural = 'My Models'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('myapp:detail', kwargs={'pk': self.pk})
```

### API Design Conventions

**Public API in api.py**:
```python
"""
Public API for the myapp Django app.
"""
from typing import Optional, List
from django.contrib.auth.models import User
from .models import MyModel


def get_mymodel_by_id(mymodel_id: int) -> Optional[MyModel]:
    """
    Retrieve a MyModel instance by ID.

    Arguments:
        mymodel_id: The ID of the MyModel instance

    Returns:
        MyModel instance or None if not found
    """
    try:
        return MyModel.objects.get(pk=mymodel_id)
    except MyModel.DoesNotExist:
        return None


def create_mymodel(name: str, user: User) -> MyModel:
    """
    Create a new MyModel instance.

    Arguments:
        name: The name for the new instance
        user: The user creating the instance

    Returns:
        The newly created MyModel instance
    """
    return MyModel.objects.create(name=name, created_by=user)
```

### Documentation Conventions

**Python docstrings** (Google style):
```python
def my_function(arg1, arg2):
    """
    Brief description of function.

    Longer description if needed, with usage examples.

    Arguments:
        arg1 (str): Description of arg1
        arg2 (int): Description of arg2

    Returns:
        bool: Description of return value

    Raises:
        ValueError: When validation fails
    """
    pass
```

**JavaScript comments** (JSDoc style):
```javascript
/**
 * Brief description of function.
 * @param {string} arg1 - Description of arg1
 * @param {number} arg2 - Description of arg2
 * @returns {boolean} Description of return value
 */
function myFunction(arg1, arg2) {
    // Implementation
}
```

### Event Tracking

Use the event tracking system for analytics:

```python
from eventtracking import tracker

# Emit an event
tracker.emit(
    'myapp.event_name',
    {
        'user_id': user.id,
        'course_id': str(course_id),
        'action': 'some_action',
    }
)
```

### Feature Flags

Check feature flags before using features:

```python
from django.conf import settings

if settings.FEATURES.get('MY_NEW_FEATURE', False):
    # New feature code
    pass
else:
    # Existing code
    pass
```

### Logging

Use structured logging:

```python
import logging

log = logging.getLogger(__name__)

# Log levels
log.debug('Debug information')
log.info('Informational message')
log.warning('Warning message')
log.error('Error message', exc_info=True)
log.exception('Exception occurred')  # Automatically includes traceback

# Structured logging
log.info(
    'User action performed',
    extra={
        'user_id': user.id,
        'action': 'enrollment',
        'course_id': str(course_id),
    }
)
```

---

## Important References

### Documentation

- **Official Docs**: https://docs.openedx.org/projects/edx-platform
- **Developer Guide**: https://docs.openedx.org/en/latest/developers/index.html
- **ADRs**: `/docs/decisions/` - Architecture Decision Records
- **How-Tos**: `/docs/how-tos/` - Practical guides
- **API Docs**: Generated via Swagger at `/api-docs/`

### Key Decision Documents

Located in `/docs/decisions/`:

- `0002-inter-app-apis.rst` - **Inter-app API pattern (CRITICAL)**
- `0006-role-of-xblock.rst` - XBlock architecture
- `0004-managing-django-settings.rst` - Settings management
- `0011-limit-modulestore-use-in-lms.rst` - Modulestore usage patterns
- `0014-justifying-new-apps.rst` - When to create new apps

### External Resources

- **Open edX Portal**: https://openedx.org
- **Community Slack**: http://openedx.slack.com
- **Discussion Forums**: https://discuss.openedx.org
- **GitHub Issues**: https://github.com/openedx/edx-platform/issues
- **Tutor**: https://github.com/overhangio/tutor - Recommended deployment

### Important Configuration Files

- `setup.py` - Package definition, XBlock/plugin entry points
- `setup.cfg` - Tool configurations (pytest, pylint, import linter)
- `package.json` - npm scripts and JavaScript dependencies
- `Makefile` - Development task automation
- `.github/workflows/` - CI/CD pipeline definitions
- `requirements/edx/*.txt` - Python dependency specifications
- `webpack.*.config.js` - Asset build configurations

### Key Patterns to Remember

1. **Always use api.py** for inter-app communication
2. **Never import LMS from CMS** or vice versa
3. **Use XBlocks** for extensible content types
4. **Feature flag new features** before full rollout
5. **Mock external dependencies** in tests
6. **Use factories** for test data creation
7. **Run import linter** before committing
8. **Test in both LMS and CMS environments** for common code
9. **Follow the test pyramid** - heavy unit tests, lighter integration tests
10. **Document public APIs** thoroughly

---

## Quick Command Reference

```bash
# Development
make requirements                    # Install dependencies
npm run build-dev                    # Build frontend assets
./manage.py lms runserver 18000     # Start LMS
./manage.py cms runserver 18010     # Start CMS

# Testing
pytest path/test.py                 # Run Python tests
npm run test                        # Run JavaScript tests
pytest --cov --cov-config=.coveragerc-local  # With coverage

# Code Quality
pycodestyle path/                   # Style checking
pylint path/                        # Linting
mypy path/                          # Type checking
lint-imports                        # Import boundary checking

# Database
./manage.py lms migrate            # Run LMS migrations
./manage.py cms migrate            # Run CMS migrations
./manage.py lms makemigrations     # Create migrations

# Translations
make extract_translations          # Extract strings
make pull_translations             # Pull from Atlas

# Build
npm run webpack                    # Build JavaScript
npm run compile-sass               # Build CSS
make docs                          # Build documentation

# Utilities
make help                          # Show all make targets
make clean                         # Clean generated files
```

---

## Working with This Codebase

### Before Making Changes

1. **Understand the domain**: Read relevant ADRs in `/docs/decisions/`
2. **Check existing patterns**: Look at similar implementations
3. **Review the app's api.py**: Understand available interfaces
4. **Run tests**: Ensure tests pass before making changes
5. **Check feature flags**: See if feature should be flagged

### While Making Changes

1. **Follow existing patterns**: Consistency is key
2. **Use inter-app APIs**: Never reach into other apps' internals
3. **Write tests first** (TDD): Or at minimum, write tests alongside code
4. **Keep changes focused**: One logical change per commit
5. **Update documentation**: Docstrings, ADRs, and guides as needed

### After Making Changes

1. **Run tests**: `pytest` for affected areas
2. **Run quality checks**: pylint, pycodestyle, mypy
3. **Check import boundaries**: `lint-imports`
4. **Verify in both LMS and CMS**: If code is in common/
5. **Update CHANGELOG.rst**: Document user-facing changes
6. **Create meaningful commits**: Clear, descriptive commit messages

### Getting Help

- Check `/docs/` for existing documentation
- Search GitHub issues for similar problems
- Ask in the Open edX Slack community
- Post on discuss.openedx.org forums
- Reference this CLAUDE.md file for architectural guidance

---

## Version Information

- **Python**: 3.11
- **Django**: See `requirements/edx/base.txt`
- **Node.js**: See `.nvmrc`
- **React**: 16.14
- **MySQL**: 8.0
- **MongoDB**: 7.x

**Last Updated**: 2025-11-13

---

*This guide is maintained for AI assistants working on the Open edX Platform. For human developer documentation, see https://docs.openedx.org/projects/edx-platform*
