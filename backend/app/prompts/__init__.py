from .templates import task_summarization


class PromptManager:
    """Manager for handling prompt templates"""
    
    @staticmethod
    def get_task_summarization_prompts(project_name: str, tasks: list) -> tuple[str, str]:
        """Get prompts for task summarization"""
        # Format tasks for the prompt (using actual Rocketlane task structure)
        task_text = ""
        for task in tasks:
            task_name = task.get('taskName', task.get('title', 'Untitled'))
            task_text += f"- {task_name}"
            
            # Add description if available
            description = task.get('description', '')
            if description:
                task_text += f": {description}"
            task_text += "\n"
            
            # Add due date
            due_date = task.get('dueDate', task.get('due_date'))
            if due_date:
                task_text += f"  Due: {due_date}\n"
            
            # Add assignees
            assignees = task.get('assignees', {})
            members = assignees.get('members', [])
            if members:
                assignee_names = [f"{m.get('firstName', '')} {m.get('lastName', '')}".strip() or m.get('emailId', '') for m in members]
                task_text += f"  Assigned to: {', '.join(assignee_names)}\n"
            
            # Add status
            status = task.get('status', {})
            if isinstance(status, dict) and 'label' in status:
                task_text += f"  Status: {status['label']}\n"
            
            # Add priority if available
            priority = task.get('priority', {})
            if isinstance(priority, dict) and 'label' in priority:
                task_text += f"  Priority: {priority['label']}\n"
            
            task_text += "\n"
        
        system_prompt = task_summarization.TASK_SUMMARIZATION_SYSTEM
        user_prompt = task_summarization.TASK_SUMMARIZATION_USER.format(
            project_name=project_name,
            tasks=task_text
        )
        
        return system_prompt, user_prompt