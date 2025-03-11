"""
add tasks: Get different retrival to look up different task (like volume, exercise selection, rep/rep) 
with diffenent prompts in critic_prompt.py.
"""
from typing import Dict, Optional, Callable
from rag_retrieval import retrieve_and_generate, retrieve_context

class Critic:
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str,
            task_type: str = "exercise_selection",  # Changed default from "general" to "exercise_selection"
            retrieval_fn: Optional[Callable] = None,
            ):
        self.model = model
        self.role = role
        self.task = task
        self.task_type = task_type
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Default specialized instructions for different task types
        self.specialized_instructions = {
            "exercise_selection": "Focus on exercise selection appropriateness for the user",
            "rep_ranges": "Focus on whether rep ranges are optimal for the stated training goals.",
            "rpe": "Focus on whether RPE (Rating of Perceived Exertion) targets are appropriate for the user and for each exercise",
            "progression": "Focus on how the program incorporates progressive overload principles."
        }

    def get_task_query(self, program: dict[str, str | None]) -> str:
        """Generate an appropriate query based on task type and program content."""
        user_input = program['user-input']
        draft = program['draft']
        
        queries = {
            "exercise_selection": f"Are these exercises appropriate for {user_input}?",
            "rep_ranges": f"Are these rep ranges optimal for {user_input}?",
            "rpe": f"Are the RPE targets appropriate for {user_input}?",
            "progression": f"Is progression appropriately structured for {user_input}?"
        }
        
        return queries.get(self.task_type, f"Evaluate {self.task_type} in training program for {user_input}")

    def critique(
            self,
            program: dict[str, str | None],
            ) -> dict[str, str | None]:
        # Always use RAG retrieval since we no longer have the "general" option
        context = ""
        query = self.get_task_query(program)
        specialized_instructions = self.specialized_instructions.get(self.task_type, "")
        retrieval_result, _ = self.retrieval_fn(query, specialized_instructions)
        context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
        
        # Make sure 'draft' contains the actual program content
        program_content = program.get('draft')
        if isinstance(program_content, dict) and 'weekly_program' in program_content:
            # If draft is a dict with weekly_program, convert it to a string for the prompt
            import json
            program_content = json.dumps(program_content, indent=2)
        
        # Create the prompt content using the task template
        prompt_content = self.task.format(
            program_content,
            program.get('user-input', ''),
        ) + context
        
        # Format system instructions
        system_instructions = self.role.get('content', '')
        
        # Use a direct string approach instead of the chat format
        # This format is compatible with both older and newer Gemini API versions
        full_prompt = f"{system_instructions}\n\n{prompt_content}"
        
        # Call the model with the properly formatted prompt
        try:
            feedback = self.model(full_prompt)
        except Exception as e:
            print(f"Error calling the model: {e}")
            return {'feedback': f"Error in critic evaluation: {str(e)}"}
        
        # More robust none-checking
        if feedback is None or (isinstance(feedback, str) and 
                               (len(feedback.strip()) < 10 and 
                                ('none' in feedback.lower() or not feedback.strip()))):
            print('CriticAgent has no feedback') # FIXME proper logging
            return {'feedback': None}

        print(f'CriticAgent has feedback: {feedback}') # FIXME proper logging
        return {'feedback': feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        article.update(self.critique(article))

        return article
