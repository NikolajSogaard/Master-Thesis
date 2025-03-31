import json
from typing import Dict, Optional, Callable
from rag_retrieval import retrieve_and_generate

class Writer:
    def __init__(
            self,
            model,
            role: dict[str, str],
            structure: str,
            task: Optional[str] = None,
            task_revision: Optional[str] = None,
            task_progression: Optional[str] = None,  # Add task_progression parameter
            writer_type: str = "initial",  # New parameter to identify writer type
            retrieval_fn: Optional[Callable] = None,
            ):
        self.model = model
        self.role = role
        self.structure = structure
        self.task = task
        self.task_revision = task_revision
        self.task_progression = task_progression  # Store task_progression
        self.writer_type = writer_type
        self.retrieval_fn = retrieval_fn or retrieve_and_generate
        
        # Define specialized instructions only for initial writing task
        self.specialized_instructions = {
            "initial": "Focus on creating the best strength training program based on the {user_input}. Consider appropriate training splits and frequency, rep-ranges, exercises that fits the user and the order of these exercises, set volume for each week and intensity."
        }
    
    def get_retrieval_query(self, program: dict[str, str | None]) -> str:
        """Generate appropriate retrieval query based on writer type and user input"""
        # Only perform retrieval for initial type
        if self.writer_type == "initial":
            return "Best practices for designing a strength training program"
        
        # Return empty string for other types to skip retrieval
        return ""

    def write(
            self,
            program: dict[str, str | None],
            ) -> tuple[str, dict[str, str]]:
        # Get retrieval context first
        query = self.get_retrieval_query(program)
        user_input = program.get('user-input', '')
        
        # Format the retrieval instructions with user input
        retrieval_instructions = self.specialized_instructions.get(self.writer_type, "")
        if '{user_input}' in retrieval_instructions:
            retrieval_instructions = retrieval_instructions.format(user_input=user_input)
        
        # Check if we have a task for writing (for initial type)
        if not self.task:
            raise ValueError(f"Writer of type '{self.writer_type}' does not support initial program creation")
        
        # Only perform retrieval for initial writer type
        enhanced_task = self.task
        if self.writer_type == "initial" and query:
            print(f"\n--- Writer (initial) retrieving context ---")
            retrieval_result, _ = self.retrieval_fn(query, retrieval_instructions)
            context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
            # Add context to the task content
            enhanced_task = self.task + context
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': enhanced_task.format(
                    program['user-input'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        
        print(f"Generating initial program...")
        # Real LLM call
        draft = self.model(combined_prompt)
        
        # Handle case where draft is string (non-JSON response)
        if isinstance(draft, str):
            print(f"String response detected, wrapping in JSON structure")
            draft = {"weekly_program": {"Day 1": []}, "message": draft}
        
        return draft

    def revise(
            self,
            program: dict[str, str | None],
            override_type: str = None,  # Add parameter to override writer_type
            ) -> tuple[str, dict[str, str]]:
        # Use override_type if provided, otherwise fall back to self.writer_type
        current_type = override_type or self.writer_type
        
        print(f"DEBUG: Writer type: {current_type}")
        print(f"DEBUG: task_revision available: {self.task_revision is not None}")
        
        # Get appropriate revision task
        revision_task = None
        
        # Try to get the most specific revision task first
        if current_type == "revision" or current_type == "progression":
            revision_task = self.task_revision
        
        # If no task_revision found, try to use a default revision task
        if not revision_task:
            print(f"WARNING: Writer of type '{current_type}' has no task_revision defined.")
            print(f"Using backup task for revision.")
            
            # As a fallback, use the TASK_REVISION from writer_prompts.py directly
            from prompts.writer_prompts import TASK_REVISION
            revision_task = TASK_REVISION
        
        # Check if we have a task for revision
        if not revision_task:
            raise ValueError(f"Writer of type '{current_type}' does not support program revision - no suitable task found")
        
        # For progression type, ensure we preserve the original program structure
        if current_type == "progression":
            print(f"Progression mode: Will maintain exercise structure and only update suggestions")
            
            # For progression, use task_progression if available
            if self.task_progression is not None:
                print(f"Using specialized task_progression template")
                revision_task = self.task_progression
        
        # No retrieval for revision or progression
        enhanced_task_revision = revision_task
        
        prompt = [
            self.role,
            {
                'role': 'user',
                'content': enhanced_task_revision.format(
                    program['draft'],
                    program['feedback'],
                    self.structure,
                ),
            },
        ]
        # Convert prompt to a single string as expected by the Gemini API
        combined_prompt = "\n".join(item.get("content", "") if isinstance(item, dict) else str(item) for item in prompt)
        
        # For progression mode, we'll process the response differently
        is_progression_mode = (current_type == "progression")
        if is_progression_mode:
            print(f"Using progression mode: Will only update AI Progression field")
            
        print(f"Revising program based on feedback...")
        # Real LLM call for revision
        try:
            draft = self.model(combined_prompt)
            
            # For progression mode, merge the new AI Progression suggestions with the original program structure
            if is_progression_mode and isinstance(draft, dict) and 'weekly_program' in draft:
                original_program = None
                
                # Get the original program structure
                if isinstance(program['draft'], dict) and 'weekly_program' in program['draft']:
                    original_program = program['draft']['weekly_program']
                    
                # If we have both the original and new program, merge them
                if original_program is not None:
                    merged_weekly_program = {}
                    new_program = draft['weekly_program']
                    
                    # Iterate through each day in the original program
                    for day, original_exercises in original_program.items():
                        merged_weekly_program[day] = []
                        
                        # For each exercise in the original day
                        for i, original_exercise in enumerate(original_exercises):
                            # Create a copy of the original exercise
                            merged_exercise = original_exercise.copy()
                            
                            # Try to find the matching exercise in the new program
                            if day in new_program and i < len(new_program[day]):
                                new_exercise = new_program[day][i]
                                # Only copy the AI Progression/suggestion field
                                if "AI Progression" in new_exercise:
                                    merged_exercise["AI Progression"] = new_exercise["AI Progression"]
                                    merged_exercise["suggestion"] = new_exercise["AI Progression"]
                                elif "suggestion" in new_exercise:
                                    merged_exercise["suggestion"] = new_exercise["suggestion"]
                                    merged_exercise["AI Progression"] = new_exercise["suggestion"]
                            
                            merged_weekly_program[day].append(merged_exercise)
                    
                    # Replace the weekly program with our merged version
                    draft['weekly_program'] = merged_weekly_program
            
            # Handle case where draft is string (non-JSON response)
            if isinstance(draft, str):
                print(f"String response detected, attempting to fix and parse as JSON")
                try:
                    # Try to extract JSON from code blocks if present
                    if "```json" in draft:
                        json_content = draft.split("```json", 1)[1]
                        if "```" in json_content:
                            json_content = json_content.split("```", 1)[0]
                        draft = json.loads(json_content.strip())
                    elif draft.strip().startswith("{") and draft.strip().endswith("}"):
                        # Try to parse as-is
                        draft = json.loads(draft)
                    else:
                        # If can't parse, create minimal structure
                        draft = {"weekly_program": {"Day 1": []}, "message": draft}
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON response: {e}")
                    print(f"Creating fallback program structure")
                    draft = {"weekly_program": {"Day 1": []}, "message": draft}
        except Exception as e:
            print(f"Error during model call or JSON parsing: {e}")
            # Create a minimal valid structure with an error message
            draft = {
                "weekly_program": {"Day 1": []}, 
                "message": f"Error generating program: {str(e)}"
            }
        
        return draft

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        # Check if the writer_type is "progression" (for Week 2+)
        if self.writer_type == "progression" and 'feedback' in program:
            # For progression, always use the revise method with progression task
            writer_type_for_this_call = "progression"
            print(f"Using progression writer task for Week 2+")
            # No need to temporarily update writer_type, just pass it directly
            draft = self.revise(program, override_type="progression")
            
        # For initial program creation (first iteration)
        elif 'draft' not in program or program['draft'] is None:
            writer_type_for_this_call = "initial"
            print("Initial program creation - using initial writer task")
            draft = self.write(program)
            
        # For all subsequent revisions (after first iteration)
        elif 'feedback' in program:
            writer_type_for_this_call = "revision"
            print("Program revision based on feedback - using revision task")
            # No need to temporarily update writer_type, pass the override directly
            draft = self.revise(program, override_type="revision")
            
        # Fallback (shouldn't happen in normal flow)
        else:
            writer_type_for_this_call = "initial"
            print("WARNING: Unexpected state - using initial writer task as fallback")
            draft = self.write(program)

        print(f'Current draft: {draft}')  # FIXME proper logging
        program['draft'] = draft
        return program
