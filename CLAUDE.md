# Open edX Platform - AI Assistant Guide

## Overview

The **Open edX Platform** (edx-platform) is a modular monolith that powers online learning at scale. Written in Python and JavaScript, it extensively uses the Django framework. This document provides AI assistants with essential context for effectively working within this large, complex codebase.

**License:** AGPL v3
**Primary Language:** Python 3.11
**Frontend:** JavaScript (Node 20), React 16.14.0
**Official Documentation:** https://docs.openedx.org/projects/edx-platform

---

## Repository Structure

### High-Level Architecture

The repository provides two main services:

1. **LMS** (Learning Management Service) - Delivers learning content to learners
2. **CMS** (Content Management Service) - Powers Open edX Studio for content authoring

### Key Directory Layout

```
edx-platform/
├── lms/                    # Learning Management System
│   ├── djangoapps/        # LMS-specific Django applications
│   ├── envs/              # Environment-specific settings
│   ├── static/            # Static assets (JS, CSS, images)
│   ├── templates/         # Django templates
│   └── lib/               # LMS-specific libraries
│
├── cms/                    # Content Management System (Studio)
│   ├── djangoapps/        # CMS-specific Django applications
│   ├── envs/              # Environment-specific settings
│   ├── static/            # Static assets
│   └── templates/         # Django templates
│
├── openedx/               # Shared code between LMS and CMS
│   ├── core/              # Core functionality
│   │   ├── djangoapps/   # Shared Django applications
│   │   └── lib/          # Shared libraries
│   ├── features/          # Feature-specific code
│   └── testing/           # Test utilities and fixtures
│
├── common/                # Shared code across services
│   ├── djangoapps/        # Common Django applications
│   ├── static/            # Shared static assets
│   ├── templates/         # Shared templates
│   └── test/              # Common test utilities
│
├── requirements/          # Python dependencies
│   └── edx/              # edX-specific requirements files
│
├── scripts/               # Utility scripts
├── docs/                  # Documentation
│   ├── decisions/        # Architectural Decision Records (ADRs)
│   ├── concepts/         # Conceptual documentation
│   ├── how-tos/          # How-to guides
│   └── references/       # Reference documentation
│
├── webpack-config/        # Webpack configuration
└── themes/               # Theming support
```

### Important Module Boundaries

**Key Architectural Principle:** LMS and CMS are designed to be independent. Cross-imports between `lms/` and `cms/` are discouraged and tracked in `setup.cfg` under `importlinter:contract:1`.

**Shared Code Pattern:**
- Code shared between LMS and CMS belongs in `openedx/` or `common/`
- `openedx/core/djangoapps/` contains shared Django apps
- `common/djangoapps/` contains legacy shared code

---

## Technology Stack

### Backend
- **Python:** 3.11
- **Framework:** Django (see requirements for specific version)
- **Databases:**
  - MySQL 8.0 (primary database)
  - MongoDB 7.x (for course structure/modulestore)
- **Cache:** Memcached
- **Task Queue:** Celery (implied by Django patterns)

### Frontend
- **Node.js:** Version 20 (see `.nvmrc`)
- **JavaScript Frameworks:**
  - React 16.14.0
  - Backbone.js 1.6.0 (legacy)
  - jQuery 2.2.4 (legacy)
- **Build Tools:**
  - Webpack 5
  - Babel 7
  - SASS/SCSS
- **State Management:**
  - Redux 3.7.2
  - React-Redux 5.1.2
- **UI Components:**
  - @edx/paragon 2.6.4 (Open edX design system)
  - Bootstrap 4.0.0

### Testing
- **Python:** pytest, unittest
- **JavaScript:** Jest 29.7.0, Karma, Jasmine
- **Coverage:** pytest-cov, karma-coverage

### Code Quality
- **Linting:** pylint, pycodestyle, eslint (legacy)
- **Type Checking:** mypy
- **Import Checking:** import-linter
- **XSS Checking:** xsslint (custom tool)
- **PII Annotations:** code_annotations

---

## Development Workflows

### Environment Setup

**Prerequisites:**
- Ubuntu 24.04 (recommended)
- Python 3.11
- Node 20
- MySQL 8.0
- MongoDB 7.x
- Memcached

**Recommended Development Method:** Use Tutor in development mode for a fully configured environment.

### Common Commands

#### Python Dependencies
```bash
make requirements              # Install development requirements
make dev-requirements          # Install development requirements (alternative)
make base-requirements         # Install base requirements only
make test-requirements         # Install testing requirements
make upgrade                   # Upgrade all dependencies
make upgrade-package package=<name>  # Upgrade specific package
```

#### Database Migrations
```bash
make migrate                   # Run all migrations (LMS + CMS)
make migrate-lms              # Run LMS migrations only
make migrate-cms              # Run CMS migrations only

# Manual migration commands
./manage.py lms migrate
./manage.py cms migrate
```

#### Frontend Build
```bash
npm run build                 # Production build
npm run build-dev             # Development build
npm run watch                 # Watch mode for development
npm run webpack               # Build JavaScript only
npm run compile-sass          # Compile SASS only
```

#### Testing
```bash
# Python tests
pytest                        # Run pytest tests
pytest path/to/test_file.py   # Run specific test file
pytest -k test_name          # Run tests matching pattern

# JavaScript tests
npm test                      # Run all JS tests
npm run test-jest            # Run Jest tests
npm run test-karma           # Run Karma tests
npm run test-lms             # Run LMS tests
npm run test-cms             # Run CMS tests
```

#### Code Quality
```bash
make check-types             # Run mypy type checking
make lint-imports            # Check import dependencies
make pycodestyle            # Check Python style
make pii_check              # Check PII annotations
make check_keywords         # Check reserved keywords in models
```

#### Running Services
```bash
./manage.py lms runserver 18000   # Start LMS on port 18000
./manage.py cms runserver 18010   # Start CMS on port 18010
```

#### Translations
```bash
make extract_translations    # Extract translatable strings
make pull_translations       # Pull translations from Atlas
make clean_translations      # Remove existing translations
```

### Django Management Commands

The `manage.py` script requires specifying either `lms` or `cms` as the first argument:

```bash
./manage.py lms <command> [options]    # Run LMS command
./manage.py cms <command> [options]    # Run CMS command
```

Common commands:
```bash
./manage.py lms shell                  # Django shell for LMS
./manage.py lms makemigrations        # Create migrations
./manage.py lms migrate               # Run migrations
./manage.py lms collectstatic         # Collect static files
./manage.py lms createsuperuser       # Create admin user
```

---

## Testing Conventions

### Python Tests

**Framework:** pytest with Django integration

**Test File Naming:**
- `test_*.py`
- `tests_*.py`
- `*_tests.py`
- `tests.py`

**Test Location:**
- Tests should be in a `tests/` directory within each Django app
- Or as `test_*.py` files alongside the code

**Common Patterns:**
```python
from django.test import TestCase
from unittest import mock

class TestMyFeature(TestCase):
    """Test my feature functionality."""

    def setUp(self):
        """Set up test fixtures."""
        pass

    def test_something(self):
        """Test something specific."""
        assert True
```

**Test Configuration:**
- Main config: `setup.cfg` under `[tool:pytest]`
- Default settings: `DJANGO_SETTINGS_MODULE = lms.envs.test`
- Fixtures: `conftest.py` at repository root

**Running Tests:**
```bash
pytest path/to/tests                    # Run specific tests
pytest --reuse-db                       # Reuse database
pytest --nomigrations                   # Skip migrations
pytest -k test_name                     # Filter by name
```

### JavaScript Tests

**Frameworks:** Jest (modern), Karma + Jasmine (legacy)

**Test File Location:**
- Co-located with source files or in separate test directories
- Jest config: `jest.config.js`

**Running JavaScript Tests:**
```bash
npm run test-jest                       # Jest tests
npm run test-karma                      # Karma tests
npm run test-cms-vanilla                # CMS vanilla JS tests
npm run test-lms-webpack                # LMS webpack tests
```

---

## Code Quality and Standards

### Python Style

**Primary Tool:** pylint with edx-lint configuration

**Configuration Files:**
- `pylintrc` - Main pylint configuration (auto-generated by edx-lint)
- `pylintrc_tweaks` - Local customizations
- `setup.cfg` - pycodestyle, isort, pytest configuration
- `mypy.ini` - Type checking configuration

**Key Standards:**
- Line length: 120 characters (see `setup.cfg`)
- Import ordering: managed by isort
- Type hints: gradually being added, checked by mypy
- Docstrings: Required for public APIs

**Ignored Errors (from setup.cfg):**
- E501 (line too long)
- E265, E266 (comment formatting)
- E305, E402, E722, E731, E741, E743, W503, W504

### Import Guidelines

**Critical Rule:** Follow import linting contracts defined in `setup.cfg`

**Key Contracts:**
1. **LMS/CMS Independence:** `lms` and `cms` modules should not import from each other
2. **Isolated Apps:** Certain apps in `openedx.core.djangoapps` can only be imported via their `api.py` or `data.py` modules
3. **Layered Architecture:** Low-level apps should not depend on high-level apps

**Checking Imports:**
```bash
make lint-imports
lint-imports
```

### Security Considerations

**PII (Personally Identifiable Information):**
- All Django models with PII must be annotated
- Configuration: `.pii_annotations.yml`
- Check: `make pii_check`

**XSS Protection:**
- Custom XSS linting: `scripts/xsslint/`
- Configuration: `scripts/xsslint_config.py`
- Thresholds: `scripts/xsslint_thresholds.json`

**Database Keywords:**
- Reserved keywords check: `make check_keywords`
- Overrides: `db_keyword_overrides.yml`

---

## Key Conventions for AI Assistants

### 1. Understanding the Codebase Structure

**When Working on LMS Features:**
- Look in `lms/djangoapps/` for LMS-specific code
- Check `openedx/core/djangoapps/` for shared functionality
- Review `common/djangoapps/` for legacy shared code

**When Working on CMS/Studio Features:**
- Look in `cms/djangoapps/` for CMS-specific code
- Primary CMS app: `cms/djangoapps/contentstore/`

**When Adding Shared Functionality:**
- Place code in `openedx/core/djangoapps/` or `openedx/features/`
- Follow the API pattern: expose public interfaces through `api.py`
- Data structures go in `data.py`
- Never import directly from LMS or CMS in shared code

### 2. Django App Patterns

**Standard Django App Structure:**
```
myapp/
├── __init__.py
├── admin.py              # Django admin configuration
├── api.py               # Public API (required for isolated apps)
├── apps.py              # App configuration
├── data.py              # Data structures and enums
├── models.py            # Database models
├── views.py             # View functions/classes
├── urls.py              # URL routing
├── serializers.py       # DRF serializers
├── tasks.py             # Celery tasks
├── signals.py           # Django signals
├── helpers.py           # Helper functions
├── utils.py             # Utility functions
├── migrations/          # Database migrations
└── tests/              # Test files
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_api.py
```

**Best Practice:** For isolated apps (listed in setup.cfg), only import from `api.py` or `data.py`.

### 3. Settings Management

**Settings Organization:**
- Base settings: `lms/envs/common.py` or `cms/envs/common.py`
- Environment-specific: `lms/envs/production.py`, `lms/envs/development.py`, `lms/envs/test.py`
- Local overrides: Not checked into git

**Feature Flags:**
- Waffle flags: For gradual feature rollout
- Django settings: `FEATURES` dictionary
- Configuration: Check `openedx/core/djangoapps/waffle_utils/`

### 4. Static Assets

**Build Process:**
- JavaScript: Webpack (see `webpack.*.config.js`)
- Styles: SASS compiled to CSS
- Build commands: `npm run build` or `npm run build-dev`

**Asset Organization:**
- LMS static: `lms/static/`
- CMS static: `cms/static/`
- Common static: `common/static/`

**Modern vs Legacy:**
- Modern: React components with Webpack
- Legacy: Backbone/jQuery with RequireJS

### 5. Handling Migrations

**Creating Migrations:**
```bash
./manage.py lms makemigrations <app_name>
./manage.py cms makemigrations <app_name>
```

**Important:**
- Always check migration dependencies
- Test migrations on both LMS and CMS if affecting shared apps
- Run `./manage.py lms showmigrations` to see migration state

### 6. Testing Requirements

**When Adding/Modifying Code:**
1. **Add tests** for new functionality
2. **Update existing tests** if behavior changes
3. **Run relevant test suite** before committing
4. **Ensure test coverage** for critical paths

**Test Discovery:**
- Python: pytest finds tests automatically in `tests/` directories
- JavaScript: Jest/Karma configurations specify test patterns

### 7. Documentation

**Where to Document:**
- **ADRs (Architectural Decision Records):** `docs/decisions/` - Use for significant architectural choices
- **Concepts:** `docs/concepts/` - High-level explanations
- **How-tos:** `docs/how-tos/` - Step-by-step guides
- **Code comments:** For complex logic
- **Docstrings:** For all public APIs

**ADR Template:** Follow existing ADR format in `docs/decisions/`

### 8. Micro-Frontends (MFEs)

**Important:** Many frontend features have been extracted to separate MFE repositories:
- Authentication: `frontend-app-authn`
- Learner Dashboard: `frontend-app-learner-dashboard`
- Learning Experience: `frontend-app-learning`
- And many more...

**When modifying frontend:** Check if the feature is in edx-platform or a separate MFE repository.

### 9. XBlocks

**XBlock Framework:**
- XBlocks are reusable course components
- Core XBlocks: Problem types, video, HTML, etc.
- XBlock runtime: Manages XBlock lifecycle

**Key Directories:**
- XBlock mixins: `common/lib/xmodule/xmodule/`
- XBlock config: `cms/djangoapps/xblock_config/`

### 10. Common Pitfalls to Avoid

1. **Circular Imports:** Especially between LMS/CMS and shared apps
2. **Direct Database Access:** Use Django ORM and defined APIs
3. **Hardcoded URLs:** Use Django's `reverse()` function
4. **Missing Translations:** Wrap user-facing strings with translation functions
5. **Security Issues:** Validate input, escape output, use Django's security features
6. **PII Violations:** Annotate models with PII data
7. **Breaking Import Contracts:** Always run `make lint-imports`
8. **Migrations Without Dependencies:** Ensure proper migration ordering
9. **Untested Code:** Write tests for new functionality
10. **Ignoring Type Hints:** Add type hints for new code when possible

---

## Common Patterns and Anti-Patterns

### ✅ Recommended Patterns

**1. API-First Design:**
```python
# myapp/api.py
def get_user_enrollments(user):
    """
    Public API to get user enrollments.

    Args:
        user: User object

    Returns:
        QuerySet of CourseEnrollment objects
    """
    return CourseEnrollment.objects.filter(user=user)
```

**2. Using Django Signals:**
```python
# myapp/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save

@receiver(post_save, sender=MyModel)
def handle_model_save(sender, instance, created, **kwargs):
    """Handle post-save logic."""
    if created:
        # Do something for new instances
        pass
```

**3. Configuration via Settings:**
```python
from django.conf import settings

def my_feature():
    if settings.FEATURES.get('MY_FEATURE_ENABLED', False):
        # Feature logic
        pass
```

**4. Proper Test Isolation:**
```python
class TestMyView(TestCase):
    def setUp(self):
        """Create test fixtures."""
        self.user = UserFactory()
        self.course = CourseFactory()

    def test_view_access(self):
        """Test that authenticated users can access the view."""
        self.client.login(username=self.user.username, password='test')
        response = self.client.get(reverse('my_view'))
        assert response.status_code == 200
```

### ❌ Anti-Patterns to Avoid

**1. Cross-Boundary Imports:**
```python
# BAD: LMS importing from CMS
from cms.djangoapps.contentstore import something

# GOOD: Use shared code
from openedx.core.djangoapps.shared_app.api import something
```

**2. Direct Model Access Across Boundaries:**
```python
# BAD: Directly accessing models from another service
from other_app.models import SomeModel
objects = SomeModel.objects.filter(...)

# GOOD: Use the public API
from other_app.api import get_some_objects
objects = get_some_objects(filters)
```

**3. Untranslated User-Facing Strings:**
```python
# BAD
return "Hello, user!"

# GOOD
from django.utils.translation import gettext as _
return _("Hello, user!")
```

---

## Working with Existing Code

### Finding Relevant Code

**For Feature Changes:**
1. Search for related test files: `find . -name "*test*keyword*.py"`
2. Search for views: `grep -r "class.*View" lms/djangoapps/myapp/`
3. Search for URLs: `grep -r "path(" lms/djangoapps/myapp/urls.py`
4. Check documentation: `docs/` directory

**For Bug Fixes:**
1. Search for error messages in code
2. Check recent changes: `git log -p -- path/to/file`
3. Look for related tests that might be failing
4. Check GitHub issues for context

**For Understanding Data Flow:**
1. Start with models: `myapp/models.py`
2. Check APIs: `myapp/api.py`
3. Follow views: `myapp/views.py`
4. Trace tests: `myapp/tests/`

### Modifying Existing Code

**Before Making Changes:**
1. Read existing tests to understand expected behavior
2. Check for ADRs related to the component
3. Verify import linting won't be violated
4. Consider backward compatibility

**When Making Changes:**
1. Update or add tests first (TDD approach)
2. Make minimal changes to achieve the goal
3. Maintain consistent code style
4. Update docstrings and comments
5. Check for related code that might need updates

**After Making Changes:**
1. Run affected tests: `pytest path/to/tests/`
2. Run linters: `make lint-imports`, `make pycodestyle`
3. Check type hints: `make check-types`
4. Build static assets if frontend changed: `npm run build-dev`
5. Test manually in running environment if possible

---

## Getting Help

**Official Resources:**
- Documentation: https://docs.openedx.org/projects/edx-platform
- Discussion Forums: https://discuss.openedx.org
- Slack: https://openedx.slack.com
- GitHub Issues: https://github.com/openedx/edx-platform/issues

**Code-Level Help:**
- Check ADRs in `docs/decisions/` for architectural context
- Look for `README.rst` files in subdirectories
- Search for similar implementations in the codebase
- Review test files for usage examples

---

## CI/CD and GitHub Workflows

The repository uses GitHub Actions for continuous integration:

**Key Workflows:**
- `unit-tests.yml` - Run Python unit tests
- `js-tests.yml` - Run JavaScript tests
- `quality-checks.yml` - Code quality checks
- `pylint-checks.yml` - Pylint validation
- `migrations-check.yml` - Migration validation
- `lint-imports.yml` - Import linting

**Before Pushing:**
1. Ensure tests pass locally
2. Run relevant quality checks
3. Verify migrations are correct
4. Check that imports are valid

---

## Quick Reference

### Most Common Commands

```bash
# Setup
make requirements

# Testing
pytest path/to/tests/
npm test

# Quality
make lint-imports
make check-types
make pycodestyle

# Running
./manage.py lms runserver 18000
./manage.py cms runserver 18010

# Database
make migrate
./manage.py lms makemigrations app_name

# Frontend
npm run build-dev
npm run watch
```

### Most Common Files to Check

- `setup.cfg` - Testing, linting, import configuration
- `requirements/edx/development.txt` - Python dependencies
- `package.json` - JavaScript dependencies and scripts
- `Makefile` - Common development tasks
- `manage.py` - Django management entry point
- `conftest.py` - Pytest configuration and fixtures

### Quick Navigation by Task

| Task | Primary Location |
|------|------------------|
| LMS views | `lms/djangoapps/*/views.py` |
| CMS views | `cms/djangoapps/contentstore/views/` |
| Models | `*/djangoapps/*/models.py` |
| APIs | `*/djangoapps/*/api.py` |
| Tests | `*/djangoapps/*/tests/` |
| Migrations | `*/djangoapps/*/migrations/` |
| Static assets | `lms/static/`, `cms/static/`, `common/static/` |
| Templates | `lms/templates/`, `cms/templates/`, `common/templates/` |
| Settings | `lms/envs/`, `cms/envs/` |
| Documentation | `docs/` |

---

## Version Information

This guide was created for edx-platform with the following approximate versions:
- Python: 3.11
- Django: See requirements files
- Node: 20
- React: 16.14.0

Always check current `requirements/` and `package.json` for exact versions.

---

## Final Notes for AI Assistants

1. **Start Small:** Understand the specific component before making broad changes
2. **Follow Patterns:** Look for existing implementations of similar features
3. **Test Thoroughly:** This is a large platform with many edge cases
4. **Respect Boundaries:** Follow the architectural contracts (especially import linting)
5. **Document Decisions:** Significant changes should be documented
6. **Ask Questions:** If unsure about architectural decisions, seek clarification
7. **Consider Impact:** Changes may affect many users and institutions globally
8. **Security First:** This platform handles educational data and PII
9. **Performance Matters:** The platform serves millions of learners
10. **Community Standards:** Follow Open edX community contribution guidelines

---

**Last Updated:** 2025-11-13
**Repository:** https://github.com/openedx/edx-platform
**Maintainers:** See https://backstage.openedx.org/catalog/default/component/edx-platform
