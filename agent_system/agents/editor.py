import json

class Editor:
    def __init__(self, writer=None):
        self.writer = writer  # Store reference to writer

    def implement_final_feedback(self, program):
        """Implement the final round of feedback if it exists"""
        # Check if there's feedback to implement
        if program.get('feedback') and self.writer:
            print("\n=== EDITOR: Implementing final round of feedback ===")
            # Call writer's revise method to implement feedback
            try:
                revised_draft = self.writer.revise(program, override_type="revision")
                program['draft'] = revised_draft
                print("Final feedback successfully implemented")
            except Exception as e:
                print(f"Error implementing final feedback: {e}")
        return program

    def extract_weekly_program(self, program_data) -> dict:
        """
        Robustly extract weekly program data from various formats.
        Can be used to standardize previous week program data for progression tasks.
        """
        # Debug logging
        print(f"DEBUG: Extracting weekly program from data (type {type(program_data)})")
        
        weekly_program = None
        
        # Handle different program data formats
        if isinstance(program_data, dict):
            # Case 1: Dict with weekly_program key
            if 'weekly_program' in program_data:
                weekly_program = program_data['weekly_program']
            
            # Case 2: Dict with formatted field
            elif 'formatted' in program_data and isinstance(program_data['formatted'], dict):
                formatted = program_data['formatted']
                if 'weekly_program' in formatted:
                    weekly_program = formatted['weekly_program']
                else:
                    weekly_program = formatted
            
            # Case 3: Dict with draft field
            elif 'draft' in program_data:
                weekly_program = self.extract_weekly_program(program_data['draft'])
            
            # Case 4: Dict with message field containing JSON
            elif 'message' in program_data and isinstance(program_data['message'], str):
                message = program_data['message']
                try:
                    # Try to parse the message as JSON
                    parsed_message = json.loads(message)
                    if isinstance(parsed_message, dict):
                        if 'weekly_program' in parsed_message:
                            weekly_program = parsed_message['weekly_program']
                        else:
                            weekly_program = parsed_message
                except json.JSONDecodeError:
                    # Try to extract JSON from code blocks if present
                    if "```json" in message:
                        try:
                            json_content = message.split("```json", 1)[1]
                            if "```" in json_content:
                                json_content = json_content.split("```", 1)[0]
                            parsed = json.loads(json_content.strip())
                            if isinstance(parsed, dict):
                                if 'weekly_program' in parsed:
                                    weekly_program = parsed['weekly_program']
                                else:
                                    weekly_program = parsed
                        except (json.JSONDecodeError, IndexError):
                            print("DEBUG: Failed to extract JSON from code blocks")
        
        # Case 5: String input (could be JSON)
        elif isinstance(program_data, str):
            try:
                parsed = json.loads(program_data)
                if isinstance(parsed, dict):
                    weekly_program = self.extract_weekly_program(parsed)
            except json.JSONDecodeError:
                # Try to extract JSON from code blocks
                if "```json" in program_data:
                    try:
                        json_content = program_data.split("```json", 1)[1]
                        if "```" in json_content:
                            json_content = json_content.split("```", 1)[0]
                        parsed = json.loads(json_content.strip())
                        weekly_program = self.extract_weekly_program(parsed)
                    except (json.JSONDecodeError, IndexError):
                        print("DEBUG: Failed to extract JSON from string code blocks")
        
        if weekly_program is None:
            print("DEBUG: Could not extract weekly program, returning empty dict")
            weekly_program = {}
        
        return weekly_program

    def format_program(self, program: dict[str, str | None]) -> dict:
        """Ensure the program is in the correct format for the web application."""
        draft = program['draft']
        # Debug logging added to inspect draft content and type
        print("DEBUG: Editor received draft (type {}): {}".format(type(draft), draft))
        
        # Use the extract_weekly_program method to get the weekly program
        weekly_program = self.extract_weekly_program(draft)
        
        # Validate and ensure each exercise has the required fields
        validated_program = {}
        for day, exercises in weekly_program.items():
            validated_program[day] = []
            for exercise in exercises:
                # Ensure all required fields exist
                validated_exercise = {
                    "name": exercise.get("name", "Unnamed Exercise"),
                    "sets": exercise.get("sets", 3),
                    "reps": exercise.get("reps", "8-12"),
                    "target_rpe": exercise.get("target_rpe", "7-8"),
                    "rest": exercise.get("rest", "60-90 seconds"),
                    "cues": exercise.get("cues", "Focus on proper form")
                }
                
                # Handle AI Progression field for week 2+
                # First check for AI Progression (with proper capitalization)
                if "AI Progression" in exercise:
                    validated_exercise["suggestion"] = exercise["AI Progression"]
                # Then check for suggestion field
                elif "suggestion" in exercise:
                    validated_exercise["suggestion"] = exercise["suggestion"]
                # Also check for lowercase variant
                elif "ai progression" in exercise:
                    validated_exercise["suggestion"] = exercise["ai progression"]
                
                validated_program[day].append(validated_exercise)
        
        return {"weekly_program": validated_program}

    def __call__(self, program: dict[str, str | None]) -> dict[str, str | None]:
        # First implement any final feedback
        program = self.implement_final_feedback(program)
        
        # Then format the program as before
        formatted = self.format_program(program)
        # Preserve Critic feedback if available
        if 'feedback' in program:
            formatted['critic_feedback'] = program['feedback']
        # If week number is available, carry it over to the formatted output
        if 'week_number' in program:
            formatted['week_number'] = program['week_number']
        program['formatted'] = formatted
        return program
