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
        
        # Specialized instructions for initial writing
        self.specialized_instructions = {
            "initial": "Focus on creating the best strength training program based on the {user_input}. Consider appropriate training splits and frequency, rep-ranges, exercises that fits the user and the order of these exercises, set volume for each week and intensity."
        }
    
    def get_retrieval_query(self, program: dict[str, str | None]) -> str:
        # Only perform retrieval for initial type
        if self.writer_type == "initial":
            return "Best practices for designing a strength training program based on {user_input} and preferences."
        return ""

    def format_previous_week_program(self, program: dict[str, str | None]) -> str:
        """
        Format the previous week's program data specifically for progression tasks.
        This ensures the model has access to properly formatted program data.
        """
        # Get the Editor to extract the weekly program
        from .editor import Editor
        editor = Editor()
        
        previous_program = None
        
        # First try to get weekly_program from the formatted field
        if 'formatted' in program and isinstance(program['formatted'], dict):
            if 'weekly_program' in program['formatted']:
                previous_program = program['formatted']['weekly_program']

        if previous_program is None and 'draft' in program:
            previous_program = editor.extract_weekly_program(program['draft'])
        
        # If still not found, try to extract from raw program data
        if previous_program is None:
            previous_program = editor.extract_weekly_program(program)
        
        # Convert to a clean, formatted JSON string for the prompt
        if previous_program:
            formatted_output = {
                "weekly_program": previous_program
            }
            return json.dumps(formatted_output, indent=2)
        
        # Fallback: Just convert whatever we have to a string
        if isinstance(program, dict):
            return json.dumps(program, indent=2)
        return str(program)

    def write(
            self,
            program: dict[str, str | None],
            ) -> tuple[str, dict[str, str]]:
        query = self.get_retrieval_query(program)
        user_input = program.get('user-input', '')
        retrieval_instructions = self.specialized_instructions.get(self.writer_type, "")
        if '{user_input}' in retrieval_instructions:
            retrieval_instructions = retrieval_instructions.format(user_input=user_input)
        if not self.task:
            raise ValueError(f"Writer of type '{self.writer_type}' does not support initial program creation")
        enhanced_task = self.task
        if self.writer_type == "initial" and query:
            print(f"\n--- Writer (initial) retrieving context ---")
            retrieval_result, _ = self.retrieval_fn(query, retrieval_instructions)
            context = f"\nRelevant context from training literature:\n{retrieval_result}\n"
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
        
        # For progression mode, ensure we preserve the original program structure
        if current_type == "progression":
            print(f"Progression mode: Will maintain exercise structure and only update suggestions")
            
            # For progression, use task_progression if available
            if self.task_progression is not None:
                print(f"Using specialized task_progression template")
                revision_task = self.task_progression
                
                # Format the previous week program specifically for progression task
                previous_program_formatted = self.format_previous_week_program(program)
                print(f"Formatted previous week program for progression task")
                
                # Add standardized instructions for progression format
                revision_task += "\n\nFINAL FORMAT REMINDER:\n"
                revision_task += "Your response for each exercise MUST contain ONLY:\n"
                revision_task += "- One line per set with performance data: Set X:(Y reps @ Zkg, RPE W)\n"
                revision_task += "- One line with just the adjustment: [number]kg ↑ or [number] reps ↓\n"
                revision_task += "- NO additional text or explanations whatsoever\n"
        
        # No retrieval for revision or progression
        enhanced_task_revision = revision_task
        
        # Build prompt based on task type
        if current_type == "progression":
            prompt = [
                self.role,
                {
                    'role': 'user',
                    'content': enhanced_task_revision.format(
                        previous_program_formatted,  # Use properly formatted previous week data
                        program['feedback'],
                        self.structure,
                    ),
                },
            ]
        else:
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
            
            # Additional format cleanup for each exercise suggestion
            for day, exercises in draft['weekly_program'].items():
                for exercise in exercises:
                    if "suggestion" in exercise:
                        suggestion = exercise["suggestion"]
                        # Check if the suggestion isn't in our format
                        if suggestion and isinstance(suggestion, str):
                            # Extract only set data and adjustment lines
                            lines = suggestion.split('\n')
                            formatted_lines = []
                            adjustment_line = None
                            
                            # Find set data lines and one adjustment line
                            for line in lines:
                                line = line.strip()
                                if line.startswith("Set ") and "(" in line:
                                    formatted_lines.append(line)
                                elif any(marker in line for marker in ["kg ↑", "kg ↓", "reps ↑", "reps ↓"]):
                                    adjustment_line = line
                                    break
                            
                            # If we found an adjustment, add it
                            if adjustment_line:
                                formatted_lines.append(adjustment_line)
                                
                            # If we've successfully formatted the content
                            if formatted_lines:
                                exercise["suggestion"] = "\n".join(formatted_lines)
                                if "AI Progression" in exercise:
                                    exercise["AI Progression"] = "\n".join(formatted_lines)
            
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
        
        # Process the draft for progression mode to ensure exact format
        if is_progression_mode and isinstance(draft, dict) and 'weekly_program' in draft:
            # Additional format cleanup for each exercise suggestion in progression mode
            for day, exercises in draft['weekly_program'].items():
                for exercise in exercises:
                    # Handle AI Progression field or suggestion field
                    for field in ["AI Progression", "suggestion"]:
                        if field in exercise and exercise[field]:
                            suggestion = exercise[field]
                            if isinstance(suggestion, str):
                                # Check if we already have the proper format
                                has_proper_format = (
                                    suggestion.strip().startswith("Set 1:") and 
                                    "(" in suggestion and ")" in suggestion
                                )
                                
                                if has_proper_format:
                                    # Already in correct format, preserve it
                                    print(f"Preserving existing progression format")
                                    
                                    # Extract performance data lines and adjustment line
                                    lines = suggestion.strip().split('\n')
                                    performance_lines = []
                                    adjustment_line = None
                                    
                                    for line in lines:
                                        if line.strip().startswith("Set "):
                                            performance_lines.append(line.strip())
                                        elif line.strip() and not line.strip().startswith("Set "):
                                            # First non-Set line is our adjustment
                                            adjustment_line = line.strip()
                                            break
                                    
                                    # Reconstruct with proper format
                                    formatted_lines = performance_lines.copy()
                                    if adjustment_line:
                                        formatted_lines.append(adjustment_line)
                                    
                                    exercise[field] = "\n".join(formatted_lines)
                                else:
                                    # Try to extract the essential information and reformat
                                    print(f"Reformatting progression suggestion to match required format")
                                    # Look for set data patterns and adjustments
                                    import re
                                    
                                    # Try to extract rep and weight information
                                    rep_match = re.search(r'(\d+)\s*reps?', suggestion)
                                    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', suggestion)
                                    
                                    if rep_match or weight_match:
                                        # Extract previous performance if available in the original data
                                        original_performance = None
                                        if 'draft' in program and isinstance(program['draft'], dict):
                                            if 'weekly_program' in program['draft']:
                                                # Find this exercise in the original program
                                                orig_prog = program['draft']['weekly_program']
                                                if day in orig_prog:
                                                    for i, orig_ex in enumerate(orig_prog[day]):
                                                        # Match exercise by position
                                                        idx = next((i for i, e in enumerate(exercises) if e == exercise), -1)
                                                        if idx >= 0 and idx < len(orig_prog[day]):
                                                            orig_ex = orig_prog[day][idx]
                                                            if 'AI Progression' in orig_ex:
                                                                original_performance = orig_ex['AI Progression']
                                        
                                        # Use original performance lines if available
                                        performance_lines = []
                                        if original_performance and original_performance.strip().startswith("Set 1:"):
                                            for line in original_performance.strip().split('\n'):
                                                if line.strip().startswith("Set "):
                                                    performance_lines.append(line.strip())
                                        else:
                                            # Fallback to generic set data
                                            performance_lines = ["Set 1:(Performance data unavailable)"]
                                            
                                        # Create the adjustment line
                                        if rep_match and "reps" in suggestion.lower():
                                            reps = rep_match.group(1)
                                            adjustment = f"        {reps} reps ↑"
                                        elif weight_match and "kg" in suggestion.lower():
                                            weight = weight_match.group(1)
                                            adjustment = f"        {weight}kg ↑"
                                        else:
                                            # Default adjustment if we can't extract specific values
                                            adjustment = "        Maintain current weight and reps"
                                            
                                        # Combine performance data with adjustment
                                        formatted = performance_lines + [adjustment]
                                        exercise[field] = "\n".join(formatted)

            # Ensure all changes are properly applied to both fields
            for day, exercises in draft['weekly_program'].items():
                for exercise in exercises:
                    if "AI Progression" in exercise and exercise["AI Progression"]:
                        exercise["suggestion"] = exercise["AI Progression"]
                    elif "suggestion" in exercise and exercise["suggestion"]:
                        exercise["AI Progression"] = exercise["suggestion"]

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
