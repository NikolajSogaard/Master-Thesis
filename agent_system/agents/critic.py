from typing import Dict, Optional, Callable, List
from rag_retrieval import retrieve_and_generate, retrieve_context
import re

class Critic:
    """
    A critic that runs multiple specialized critiques sequentially with RAG retrieval.
    """
    def __init__(
            self,
            model,
            role: dict[str, str],
            task: str,
            task_type: str = None,  # No longer used but kept for backward compatibility
            retrieval_fn: Optional[Callable] = None,
            week1_task_types: List[str] = None,
            subsequent_week_task_types: List[str] = None,
            ):
        self.model = model
        self.role = role
        self.task = task
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Define which tasks to run in week 1 (default if not specified)
        self.week1_task_types = week1_task_types or ["exercise_selection", "rep_ranges", "rpe"]
        
        # Define which additional tasks to run in subsequent weeks (default if not specified)
        self.subsequent_week_task_types = subsequent_week_task_types or ["progression"]

    def get_task_query(self, task_type: str) -> str:
        """
        Generate a highly focused query specifically for RAG retrieval based on task type.
        This query is used to fetch relevant literature for context, not for the critique itself.
        """
        query_mapping = {
            "exercise_selection": "Most effective exercise selection criteria and alternatives for strength training",
            "rep_ranges": "Scientific evidence for optimal rep ranges in strength, hypertrophy, and endurance training",
            "rpe": "use jeff nippards guidlines to implement RPE and adjust for each exercise",
            "progression": "Effective progressive overload techniques and week-to-week progression methods"
        }
        
        # Use the specific query if available, otherwise use a general one
        return query_mapping.get(task_type, f"Best practices for {task_type} in strength training programs")

    def run_single_critique(
            self,
            program: dict[str, str | None],
            task_type: str
            ) -> str:
        """Run a single critique with RAG retrieval."""
        print(f"\n--- Running {task_type.upper()} critique ---")
        
        # Get a focused query for this task type
        query = self.get_task_query(task_type)
        
        # Retrieve relevant context with a length limit for conciseness
        print(f"Retrieving context...")
        retrieval_result, _ = self.retrieval_fn(query, "")
        
        # Extract key points from the retrieval result (bullet point format)
        key_points = []
        lines = retrieval_result.split("\n")
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:  # Only include substantial points
                # Remove any source citations or parenthetical references
                cleaned_line = re.sub(r'\([^)]*\)', '', line)
                key_points.append(f"• {cleaned_line}")
        
        # Take only the most relevant points
        context = "\nKey points from training literature:\n" + "\n".join(key_points[:5]) + "\n"
        
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
        full_prompt = f"{system_instructions}\n\n{prompt_content}"
        
        print(f"Generating critique...")
        # Call the model with the properly formatted prompt
        try:
            feedback = self.model(full_prompt)
            return feedback if feedback else None
        except Exception as e:
            print(f"Error in {task_type.upper()} critique: {e}")
            return f"Error in {task_type} critique: {str(e)}"

    def is_subsequent_week(self, program: dict[str, str | None]) -> bool:
        """Determine if this is a subsequent week (Week 2+) program."""
        # Check for explicit week field
        if 'week' in program and program['week'] > 1:
            return True
            
        # Check user input for week references
        user_input = program.get('user-input', '')
        if isinstance(user_input, str):
            # Look for patterns like "Week 2", "Week 3", etc.
            week_match = re.search(r'Week\s+(\d+)', user_input, re.IGNORECASE)
            if week_match and int(week_match.group(1)) > 1:
                return True
                
            # Look for phrases indicating subsequent weeks
            if re.search(r'next week|following week|subsequent week', user_input, re.IGNORECASE):
                return True
            
        return False

    def critique(self, program: dict[str, str | None]) -> dict[str, str | None]:
        """Run each critique type sequentially with its own RAG retrieval."""
        print("\n========== CRITIQUE PROCESS STARTED ==========")
        all_feedback = []
        
        # Determine which task types to run based on whether this is a subsequent week
        task_types = self.week1_task_types.copy()
        if self.is_subsequent_week(program):
            print(f"Detected subsequent week - adding tasks: {self.subsequent_week_task_types}")
            task_types.extend(self.subsequent_week_task_types)
        else:
            print(f"First week program - using only week 1 tasks: {self.week1_task_types}")
        
        # Run each applicable task type with its own specialized retrieval
        for task_type in task_types:
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
        print(f"\n========== CRITIQUE PROCESS COMPLETE ({len(all_feedback)}/{len(task_types)}) ==========")
        return {'feedback': combined_feedback}

    def __call__(self, article: dict[str, str | None]) -> dict[str, str | None]:
        """Make the Critic callable."""
        article.update(self.critique(article))
        return article
