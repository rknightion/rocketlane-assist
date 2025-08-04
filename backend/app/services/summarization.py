from typing import Dict, Any, List
from ..core.llm import get_llm_provider
from ..services.rocketlane import RocketlaneClient
from ..prompts import PromptManager


class SummarizationService:
    """Service for summarizing tasks and projects"""
    
    def __init__(self):
        self.rocketlane_client = RocketlaneClient()
        self.prompt_manager = PromptManager()
    
    async def summarize_project_tasks(self, project_id: str) -> Dict[str, Any]:
        """Summarize outstanding tasks for a project"""
        # Get project details
        project = await self.rocketlane_client.get_project(project_id)
        project_name = project.get("projectName", project.get("name", "Unknown Project"))
        
        # Get outstanding tasks (not done)
        tasks = await self.rocketlane_client.get_project_tasks(
            project_id=project_id,
            status="not_done"  # Adjust based on actual Rocketlane API
        )
        
        if not tasks:
            return {
                "project_id": project_id,
                "project_name": project_name,
                "summary": "No outstanding tasks found for this project.",
                "task_count": 0
            }
        
        # Get prompts
        system_prompt, user_prompt = self.prompt_manager.get_task_summarization_prompts(
            project_name=project_name,
            tasks=tasks
        )
        
        # Generate summary using LLM
        llm_provider = get_llm_provider()
        summary = await llm_provider.generate_completion(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        
        return {
            "project_id": project_id,
            "project_name": project_name,
            "summary": summary,
            "task_count": len(tasks),
            "tasks": tasks  # Include tasks for reference
        }