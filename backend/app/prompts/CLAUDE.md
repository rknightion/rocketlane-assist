# AI Prompt Templates

## Template Structure
```python
# prompts/templates/example.py
TEMPLATE = """
System context: {context}

User input: {input}

Instructions:
1. Analyze the input
2. Provide structured output
3. Include confidence score
"""

def build_prompt(context: str, input: str) -> str:
    return TEMPLATE.format(context=context, input=input)
```

## Task Summarization
- **Template**: `task_summarization.py`
- **Input**: List of tasks with status, assignee, dates
- **Output**: Status overview, risks, next actions  
- **Token limit**: ~2000 tokens max

## Available Templates
- `task_summarization.py` - Project task analysis
- `risk_assessment.py` - Risk identification (planned)
- `timeline_generation.py` - Timeline creation (planned)

## Template Rules
- **Parameterized** - use `.format()` or f-strings
- **Token conscious** - include length estimates
- **Structured output** - request JSON when possible
- **Context injection** - include relevant project data
- **User-specific** - filter content by selected user