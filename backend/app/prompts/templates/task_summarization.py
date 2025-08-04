TASK_SUMMARIZATION_SYSTEM = """You are a helpful assistant that summarizes project tasks.
Your goal is to provide clear, concise summaries of outstanding tasks that help project managers and team members understand what needs to be done.
Focus on clarity, priority, and actionability."""

TASK_SUMMARIZATION_USER = """Please summarize the following outstanding tasks for the project:

Project: {project_name}

Tasks:
{tasks}

Please provide:
1. A brief overview of the current project status based on outstanding tasks
2. Key priorities that need immediate attention
3. Any potential blockers or dependencies you notice
4. A concise summary suitable for sharing with stakeholders

Keep the summary professional and actionable."""