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

    def format_program(self, program: dict[str, str | None]) -> dict:
        """Ensure the program is in the correct format for the web application."""
        draft = program['draft']
        # Debug logging added to inspect draft content and type
        print("DEBUG: Editor received draft (type {}): {}".format(type(draft), draft))
        
        weekly_program = None
        
        # Case 1: If draft is already a dict with 'weekly_program' key
        if isinstance(draft, dict) and 'weekly_program' in draft:
            weekly_program = draft['weekly_program']
        
        # Case 2: If draft is a dict with a message field containing JSON
        elif isinstance(draft, dict) and 'message' in draft and isinstance(draft['message'], str):
            message = draft['message']
            try:
                # Try to parse the message as JSON
                parsed_message = json.loads(message)
                if isinstance(parsed_message, dict) and 'weekly_program' in parsed_message:
                    print("DEBUG: Successfully extracted weekly_program from message field")
                    weekly_program = parsed_message['weekly_program']
                elif isinstance(parsed_message, dict):
                    print("DEBUG: Message field parsed as dict but missing weekly_program")
                    weekly_program = parsed_message
            except json.JSONDecodeError:
                print("DEBUG: Message field is not valid JSON, continuing with other cases")
        
        # Case 3: If draft is a dict but missing 'weekly_program' key
        elif isinstance(draft, dict):
            weekly_program = draft
        
        # Case 4: If draft is a string, try to parse it as JSON
        elif isinstance(draft, str):
            try:
                parsed = json.loads(draft)
                # If parsed JSON has 'weekly_program' key
                if isinstance(parsed, dict) and 'weekly_program' in parsed:
                    weekly_program = parsed['weekly_program']
                # If parsed JSON is missing 'weekly_program' key
                elif isinstance(parsed, dict):
                    weekly_program = parsed
            except json.JSONDecodeError:
                # If string is not valid JSON, try to extract JSON from code blocks
                if "```json" in draft:
                    try:
                        json_content = draft.split("```json", 1)[1]
                        if "```" in json_content:
                            json_content = json_content.split("```", 1)[0]
                        parsed = json.loads(json_content.strip())
                        if isinstance(parsed, dict) and 'weekly_program' in parsed:
                            weekly_program = parsed['weekly_program']
                        elif isinstance(parsed, dict):
                            weekly_program = parsed
                    except (json.JSONDecodeError, IndexError):
                        print("DEBUG: Failed to extract JSON from code blocks")
        
        if weekly_program is None:
            weekly_program = {}
        
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
                if "AI Progression" in exercise:
                    validated_exercise["suggestion"] = exercise["AI Progression"]
                elif "suggestion" in exercise:
                    validated_exercise["suggestion"] = exercise["suggestion"]
                
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
