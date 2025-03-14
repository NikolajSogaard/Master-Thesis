from typing import Dict, Optional, Callable, List
from rag_retrieval import retrieve_and_generate, retrieve_context

class Critic:
    """
    A critic that runs multiple specialized critiques sequentially with RAG retrieval.
    """
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str = None,
            tasks: Dict[str, str] = None,  # New parameter for task templates by type
            task_type: str = None,  # No longer used but kept for backward compatibility
            retrieval_fn: Optional[Callable] = None,
            ):
        self.model = model
        self.role = role
        self.task = task  # Keep for backward compatibility
        self.tasks = tasks or {}  # Dictionary of task templates by task type
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Default specialized instructions for different task types
        self.specialized_instructions = {
            "frequency": "Focus on whether the program stimulates each muscle group at least two times a week",
            "exercise_selection": "Focus on exercise selection appropriateness for the user level, find inspiration from training programs in the literature.",
            "rep_ranges": "Focus on whether rep ranges are optimal for the users training goals.",
            "rpe": "Focus on whether RPE (Rating of Perceived Exertion) targets are appropriate for the user and for each exercise",
            "progression": "Focus on how the program incorporates progressive overload principles."
        }
        
        # Define all task types to always run
        self.task_types = ["frequency", "exercise_selection", "rep_ranges", "rpe"]

    def get_task_query(self, program: dict[str, str | None], task_type: str) -> str:
        """Generate an appropriate query based on task type without including user input."""
        
        queries = {
            "frequency": "What makes training frequency appropriate for strength training programs?",
            "exercise_selection": "What makes exercise selection appropriate for strength training programs?",
            "rep_ranges": "What are optimal rep ranges for different strength training goals?",
            "rpe": "How to determine appropriate RPE targets based on exercise type and experience level?",
            "progression": "What are effective progression principles in strength training programs?"
        }
        
        return queries.get(task_type, f"Best practices for {task_type} in strength training programs")

    def run_single_critique(
            self,
            program: dict[str, str | None],
            task_type: str
            ) -> str:
        """Run a single critique with specialized RAG retrieval."""
        print(f"\n--- Running {task_type.upper()} critique ---")
        
        # Get query and instructions for this task type
        query = self.get_task_query(program, task_type)
        specialized_instructions = self.specialized_instructions.get(task_type, "")
        
        # Retrieve relevant context with specialized instructions
        print(f"Retrieving context...")
        retrieval_result, _ = self.retrieval_fn(query, specialized_instructions)
        context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
        
        # Make sure 'draft' contains the actual program content
        program_content = program.get('draft')
        if isinstance(program_content, dict) and 'weekly_program' in program_content:
            # If draft is a dict with weekly_program, convert it to a string for the prompt
            import json
            program_content = json.dumps(program_content, indent=2)
        
        # Use the specific task template for this task_type if available
        # Otherwise fall back to the general task template
        task_template = self.tasks.get(task_type, self.task)
        if task_template is None:
            # If no template is available, use a default format
            task_template = f'''
            Your colleague has written the following training program:
            {{}}
            For an individual who provided the following input:
            {{}}
            Focus specifically on the {task_type.upper()}. Provide feedback if any... otherwise only return "None"
            '''
        
        # Create the prompt content using the task template
        prompt_content = task_template.format(
            program_content,
            program.get('user-input', ''),
        ) + context
        
        # Format system instructions
        system_instructions = self.role.get('content', '')
        
        # Use a direct string approach instead of the chat format
        # This format is compatible with both older and newer Gemini API versions
        full_prompt = f"{system_instructions}\n\n{prompt_content}"
        
        print(f"Generating critique...")
        # Call the model with the properly formatted prompt
        try:
            feedback = self.model(full_prompt)
            return feedback if feedback else None
        except Exception as e:
            print(f"Error in {task_type.upper()} critique: {e}")
            return f"Error in {task_type} critique: {str(e)}"

    def critique(self, program: dict[str, str | None]) -> dict[str, str | None]:
        """Run each critique type sequentially with its own RAG retrieval."""
        print("\n========== CRITIQUE PROCESS STARTED ==========")
        all_feedback = []
        
        # Run each task type with its own specialized retrieval
        for task_type in self.task_types:
            feedback = self.run_single_critique(program, task_type)
            
            if feedback and isinstance(feedback, str) and feedback.lower() != 'none' and len(feedback.strip()) > 10:
                # Add the formatted feedback with task type header
                formatted_feedback = f"[{task_type.upper()} FEEDBACK]:\n{feedback}\n"
                all_feedback.append(formatted_feedback)
                
                # Display the actual feedback in the terminal with clear formatting
                print(f"\n{'='*50}")
                print(f"{task_type.upper()} CRITIQUE:")
                print(f"{'='*50}")
                # Print the feedback with a max width for readability
                words = feedback.split()
                line = ""
                for word in words:
                    if len(line) + len(word) > 80:
                        print(line)
                        line = word + " "
                    else:
                        line += word + " "
                if line:
                    print(line)
                print(f"{'='*50}\n")
            else:
                print(f"\n{task_type.upper()} - No significant feedback provided")
        
        if not all_feedback:
            print('No feedback from any critique tasks')
            return {'feedback': None}
        
        # Combine all feedback with section headers
        combined_feedback = "\n".join(all_feedback)
        print(f"\n========== CRITIQUE PROCESS COMPLETE ({len(all_feedback)}/{len(self.task_types)}) ==========")
        return {'feedback': combined_feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        """Make the Critic callable."""
        article.update(self.critique(article))
        return article
