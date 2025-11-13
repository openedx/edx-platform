# AI-Powered Adaptive Learning System for Open edX

This package implements an intelligent, adaptive learning system that integrates with Open edX to provide personalized education at scale.

## Overview

The AI-Powered Adaptive Learning System consists of two main components:

1. **Open edX Integration** (this package) - Django app and XBlocks that integrate with the Open edX platform
2. **AI Engine** (separate repository) - FastAPI microservices that provide the intelligence layer

## Features

### For Students

- **Adaptive Assessments**: Questions that adapt based on performance with personalized feedback
- **AI Tutor**: Real-time chat interface for getting help and explanations
- **Personalized Learning Paths**: Content automatically adjusts to student needs
- **Learning Style Recognition**: System adapts to visual, auditory, kinesthetic preferences

### For Instructors

- **AI-Powered Course Generation**: Create entire courses from natural language prompts
- **Automated Content Creation**: Generate lessons, assessments, and examples using LLMs
- **Learning Analytics**: Deep insights into student learning patterns
- **Adaptive Interventions**: Automated support for struggling students

## Architecture

```
┌─────────────────────────────────────────┐
│        Open edX Platform                 │
│  ┌───────────────────────────────────┐  │
│  │  Custom XBlocks                   │  │
│  │  • Adaptive Assessment            │  │
│  │  • AI Tutor Chat                  │  │
│  └───────────────┬───────────────────┘  │
│                  │                       │
│  ┌───────────────▼───────────────────┐  │
│  │  Django Integration App           │  │
│  │  (openedx.features.ai_learning)   │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼───────────────────────┘
                   │ REST API
┌──────────────────▼───────────────────────┐
│           AI Engine                       │
│  (FastAPI Microservices)                 │
│  • Curriculum Generator                  │
│  • Content Creator                       │
│  • Student Modeler                       │
│  • Adaptation Engine                     │
└──────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Open edX Tutor installation (Olive release or later recommended)
- Python 3.11+
- Access to LLM APIs (Google Gemini, Anthropic Claude, or OpenAI)

### Step 1: Install the Django Integration

This package is included in the `openedx/features/` directory of edx-platform.

1. Add to your LMS settings (lms.yml or environment.json):

```yaml
AI_ENGINE_BASE_URL: "http://ai-engine:8001"
AI_ENGINE_API_KEY: "your-api-key-here"
AI_ENGINE_TIMEOUT: 30

FEATURES:
  ENABLE_AI_LEARNING: true
  ENABLE_AI_TUTOR: true
  ENABLE_ADAPTIVE_ASSESSMENT: true

AI_LLM_PROVIDER: "gemini"  # or "claude", "openai"
AI_LLM_MODEL: "gemini-2.0-flash-exp"
```

2. Run migrations:

```bash
./manage.py lms migrate ai_learning
./manage.py cms migrate ai_learning
```

3. Collect static assets:

```bash
npm run build
./manage.py lms collectstatic --noinput
./manage.py cms collectstatic --noinput
```

### Step 2: Deploy the AI Engine

See the [AI Engine Implementation Guide](../../docs/how-tos/ai-engine-implementation-guide.rst) for detailed instructions on deploying the FastAPI microservices.

Quick start with Docker:

```bash
cd /path/to/ai-engine
cp .env.example .env
# Edit .env with your API keys and configuration
docker-compose up -d
```

### Step 3: Configure Webhooks

The AI Engine needs to send webhooks back to Open edX. Configure the webhook URL in your AI Engine settings:

```bash
OPENEDX_BASE_URL=https://your-openedx-instance.org
OPENEDX_WEBHOOK_SECRET=your-secret-here
```

In Open edX, set the corresponding webhook secret:

```yaml
AI_LEARNING_WEBHOOK_SECRET: "your-secret-here"
```

## Usage

### For Course Creators

#### Generate an AI-Powered Course

1. Go to Studio
2. Create a new course (or use existing)
3. Use the Open edX API or Django admin to trigger course generation:

```python
from openedx.features.ai_learning import api as ai_api

ai_course = ai_api.generate_course(
    user=request.user,
    prompt="Create a comprehensive undergraduate course on Machine Learning covering supervised learning, unsupervised learning, and neural networks",
    course_org="UniversityX",
    course_number="CS229",
    course_run="2025_Spring",
    metadata={
        "level": "undergraduate",
        "duration_weeks": 12,
        "prerequisites": ["Python programming", "Linear Algebra", "Calculus"]
    }
)
```

#### Add Adaptive Assessments

1. In Studio, add a new component to your course
2. Select "Adaptive Assessment" from the XBlock list
3. Configure:
   - Question text
   - Question type (multiple choice, short answer, numeric)
   - Answer options
   - Enable/disable AI feedback

#### Add AI Tutor

1. In Studio, add a new component
2. Select "AI Tutor" from the XBlock list
3. Configure:
   - Tutor persona (friendly mentor, Socratic teacher, expert, peer)
   - Welcome message
   - Conversation history settings

### For Students

#### Interact with Adaptive Assessments

1. Navigate to a lesson with an Adaptive Assessment
2. Read the question and submit your answer
3. Receive personalized feedback based on your learning profile
4. The system automatically adjusts future content based on performance

#### Chat with AI Tutor

1. Navigate to a lesson with an AI Tutor
2. Type your question in the chat interface
3. Receive contextual help based on:
   - Current lesson content
   - Your learning history
   - Your learning style preferences

## API Reference

### Generate Course

```
POST /ai-learning/api/v1/courses/generate/
```

Request body:
```json
{
  "prompt": "Create a PhD-level course on Quantum Field Theory",
  "course_org": "MIT",
  "course_number": "8.323",
  "course_run": "2025_Spring",
  "metadata": {
    "level": "phd",
    "duration_weeks": 16
  }
}
```

### Record Interaction

```
POST /ai-learning/api/v1/interactions/record/
```

Request body:
```json
{
  "course_key": "course-v1:edX+DemoX+Demo_Course",
  "usage_key": "block-v1:edX+DemoX+Demo_Course+type@problem+block@...",
  "interaction_type": "assessment",
  "interaction_data": {
    "score": 0.85,
    "time_spent": 120,
    "attempts": 2
  }
}
```

### Get Adaptive Feedback

```
POST /ai-learning/api/v1/feedback/
```

Request body:
```json
{
  "course_key": "course-v1:edX+DemoX+Demo_Course",
  "usage_key": "block-v1:...",
  "question": {
    "text": "What is 2 + 2?",
    "type": "numeric"
  },
  "answer": {
    "value": "5",
    "time_taken": 15000
  }
}
```

### AI Tutor Chat

```
POST /ai-learning/api/v1/tutor/chat/
```

Request body:
```json
{
  "course_key": "course-v1:edX+DemoX+Demo_Course",
  "usage_key": "block-v1:...",
  "message": "Can you explain quantum entanglement in simpler terms?",
  "conversation_history": []
}
```

## Configuration Reference

### Django Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `AI_ENGINE_BASE_URL` | Base URL of AI Engine API | `http://localhost:8001` |
| `AI_ENGINE_API_KEY` | API key for authentication | - |
| `AI_ENGINE_TIMEOUT` | Request timeout in seconds | `30` |
| `AI_LLM_PROVIDER` | LLM provider (gemini/claude/openai) | `gemini` |
| `AI_LLM_MODEL` | Model name | `gemini-2.0-flash-exp` |
| `AI_ENGINE_RATE_LIMIT` | Rate limit for API calls | `100/hour` |
| `AI_LEARNING_WEBHOOK_SECRET` | Secret for webhook validation | - |

### Feature Flags

| Flag | Description | Default |
|------|-------------|---------|
| `ENABLE_AI_LEARNING` | Enable AI learning features | `False` |
| `ENABLE_AI_TUTOR` | Enable AI tutor XBlock | `False` |
| `ENABLE_ADAPTIVE_ASSESSMENT` | Enable adaptive assessment XBlock | `False` |

## Data Models

### AIGeneratedCourse

Tracks AI-generated courses.

Fields:
- `course_key` - Course identifier
- `creator` - User who requested generation
- `generation_prompt` - Original prompt
- `generation_status` - Status (pending/generating/completed/failed)
- `curriculum_data` - Structured curriculum
- `ai_engine_course_id` - ID in AI Engine system

### StudentLearningProfile

Stores student learning profiles.

Fields:
- `user` - Student user
- `ai_engine_profile_id` - Profile ID in AI Engine
- `learning_style` - Identified learning style
- `mastered_concepts` - List of mastered concepts
- `struggling_concepts` - List of struggling concepts
- `preferences` - Learning preferences

### AdaptiveInteraction

Logs adaptive interactions.

Fields:
- `user` - Student user
- `course_key` - Course identifier
- `usage_key` - XBlock identifier
- `interaction_type` - Type (assessment/tutor_chat/etc.)
- `interaction_data` - Interaction data
- `ai_response` - AI Engine response
- `response_time_ms` - Response time

## Development

### Running Tests

```bash
# Python tests
pytest openedx/features/ai_learning/tests/ -v

# JavaScript tests (for XBlocks)
npm run test

# Integration tests
pytest openedx/features/ai_learning/tests/integration/ -v
```

### Code Quality

```bash
# Linting
pylint openedx/features/ai_learning/

# Type checking
mypy openedx/features/ai_learning/

# Import checking
make lint-imports
```

### Debugging

Enable debug logging in your settings:

```python
LOGGING = {
    'loggers': {
        'openedx.features.ai_learning': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Troubleshooting

### AI Engine Connection Issues

**Problem**: "Unable to connect to AI Engine"

**Solution**:
1. Verify AI Engine is running: `curl http://ai-engine:8001/api/v1/health`
2. Check `AI_ENGINE_BASE_URL` setting
3. Verify network connectivity between Open edX and AI Engine
4. Check API key configuration

### Webhook Failures

**Problem**: Webhooks from AI Engine are rejected

**Solution**:
1. Verify `AI_LEARNING_WEBHOOK_SECRET` matches on both sides
2. Check webhook signature validation
3. Review webhook logs in Django admin

### LLM API Issues

**Problem**: "LLM request failed" or timeout errors

**Solution**:
1. Verify API keys are correct in AI Engine
2. Check LLM provider rate limits
3. Increase `AI_ENGINE_TIMEOUT` if requests are slow
4. Monitor LLM API status

### XBlock Not Showing

**Problem**: Custom XBlocks don't appear in Studio

**Solution**:
1. Verify feature flags are enabled
2. Run `./manage.py cms lms collectstatic`
3. Restart LMS/CMS services
4. Check XBlock registration in Studio

## Performance Considerations

- **Caching**: The system caches student profiles and AI responses (5-minute TTL by default)
- **Rate Limiting**: Configure rate limits to prevent LLM API overuse
- **Async Processing**: Long-running operations (course generation) are handled asynchronously
- **Database Indexes**: Ensure proper indexing for large-scale deployments

## Security

- All API communication uses HTTPS in production
- API keys are stored encrypted in Django settings
- Webhook payloads are validated with HMAC signatures
- Student data is handled per FERPA/GDPR requirements
- PII is properly annotated in models

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This software is licensed under the AGPL v3 license. See the LICENSE file for details.

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Report at https://github.com/openedx/edx-platform/issues
- **Discussions**: https://discuss.openedx.org
- **Slack**: https://openedx.slack.com

## Roadmap

- [ ] Multi-modal content support (video, audio, interactive simulations)
- [ ] Collaborative learning features (AI-facilitated study groups)
- [ ] Learning analytics dashboard for instructors
- [ ] Mobile app integration
- [ ] Accessibility enhancements (text-to-speech, simplification)
- [ ] Multi-language support with translation

## Credits

Developed for the Open edX community to advance personalized, adaptive learning at scale.

**Maintainers**: See MAINTAINERS file

**Contributors**: See CONTRIBUTORS file
