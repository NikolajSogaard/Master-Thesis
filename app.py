from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session
import json
import os
import argparse
import tempfile
from datetime import datetime, timedelta
import uuid

from agent_system import (
    setup_llm,
    ProgramGenerator,
    Writer,
    Critic,
    Editor,
)

from prompts import (
    WriterPromptSettings,
    CriticPromptSettings,
    WRITER_PROMPT_SETTINGS,
    CRITIC_PROMPT_SETTINGS,
)

from rag_retrieval import retrieve_and_generate

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure server-side sessions
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(tempfile.gettempdir(), "flask_session_files")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)
app.config["SESSION_USE_SIGNER"] = True
Session(app) # initialize session management

DEFAULT_CONFIG = {
    'model': 'gemini-2.5-pro-preview-03-25',
    'max_tokens': 8000,
    'writer_temperature': 0.4,
    'writer_top_p': 0.9,
    'writer_prompt_settings': 'v1',
    'critic_prompt_settings': 'week1',
    'max_iterations': 1
}

def get_program_generator(config=None):
    """Setup the program generator with the given or default config"""
    if config is None:
        config = DEFAULT_CONFIG
    
    # Setup prompt settings based on week/task
    week_number = config.get('week_number', 1)
    is_revision = config.get('is_revision', False)
    writer_type = "initial" 
    if week_number > 1:
        writer_type = "progression"
    elif is_revision:
        writer_type = "revision"

    writer_prompt_settings = WRITER_PROMPT_SETTINGS[writer_type]
    print(f"DEBUG: Writer type selected: {writer_type}")

    critic_setting_key = 'progression' if week_number > 1 else 'week1'
    critic_prompt_settings = CRITIC_PROMPT_SETTINGS[critic_setting_key]
    
    # LLMs
    llm_writer = setup_llm(
        model=config['model'],
        respond_as_json=True,
        temperature=config['writer_temperature'],
        top_p=config['writer_top_p'],
    )
    llm_critic = setup_llm(
        model=config['model'],
        max_tokens=config['max_tokens'],
        respond_as_json=False,
    )

    all_revision_tasks = {}
    for type_key, settings in WRITER_PROMPT_SETTINGS.items():
        if settings.task_revision:
            all_revision_tasks[type_key] = settings.task_revision

    task_revision = writer_prompt_settings.task_revision
    if not task_revision and 'revision' in WRITER_PROMPT_SETTINGS:
        task_revision = WRITER_PROMPT_SETTINGS['revision'].task_revision
    
    # Agents
    writer = Writer(
        model=llm_writer,
        role=writer_prompt_settings.role,
        structure=writer_prompt_settings.structure,
        task=writer_prompt_settings.task,
        task_revision=task_revision,
        task_progression=getattr(writer_prompt_settings, 'task_progression', None),
        writer_type=writer_type,
        retrieval_fn=retrieve_and_generate # Retrieval function
    )

    critic = Critic(
        model=llm_critic,
        role=critic_prompt_settings.role,
        tasks=getattr(critic_prompt_settings, 'tasks', None),
        retrieval_fn=retrieve_and_generate
    )

    editor = Editor()

    return ProgramGenerator(
        writer=writer,
        critic=critic,
        editor=editor,
        max_iterations=config.get('max_iterations', 2)
    )

def parse_program(program_output):
    """Parse the program output into a structured format for the template"""
    print(f"DEBUG: parse_program received: {type(program_output)}")
    print(f"DEBUG: program_output content: {program_output}")
    try:
        if isinstance(program_output, str):
            try:
                program_output = json.loads(program_output)
                print(f"DEBUG: Parsed string to JSON: {type(program_output)}")
            except json.JSONDecodeError:
                print(f"DEBUG: Failed to parse string as JSON")

        if isinstance(program_output, dict):
            if 'weekly_program' in program_output:
                print(f"DEBUG: Found weekly_program directly")
                return program_output['weekly_program']

            if 'formatted' in program_output:
                formatted = program_output['formatted']
                print(f"DEBUG: Found formatted field (type {type(formatted)})")

                if isinstance(formatted, str):
                    try:
                        parsed = json.loads(formatted)
                        if 'weekly_program' in parsed:
                            print(f"DEBUG: Found weekly_program in parsed formatted string")
                            return parsed['weekly_program']
                        return parsed
                    except json.JSONDecodeError:
                        print(f"DEBUG: Failed to parse formatted string")

                elif isinstance(formatted, dict):
                    if 'weekly_program' in formatted:
                        print(f"DEBUG: Found weekly_program in formatted dict")
                        return formatted['weekly_program']
                    print(f"DEBUG: Returning formatted dict directly")
                    return formatted

            if 'message' in program_output and isinstance(program_output['message'], str):
                print(f"DEBUG: Checking message field for JSON")
                try:
                    message_content = program_output['message']

                    if "```json" in message_content:
                        json_content = message_content.split("```json", 1)[1]
                        if "```" in json_content:
                            json_content = json_content.split("```", 1)[0]
                        message_content = json_content.strip()

                    if message_content.strip().startswith("{") and message_content.strip().endswith("}"):
                        parsed_message = json.loads(message_content)
                        if isinstance(parsed_message, dict):
                            if 'weekly_program' in parsed_message:
                                print(f"DEBUG: Found weekly_program in message JSON")
                                return parsed_message['weekly_program']
                            print(f"DEBUG: Returning parsed message directly")
                            return parsed_message
                except (json.JSONDecodeError, IndexError) as e:
                    print(f"DEBUG: Failed to extract JSON from message: {e}")

            if 'draft' in program_output:
                print(f"DEBUG: Checking draft field")
                draft = program_output['draft']

                if isinstance(draft, dict):
                    if 'weekly_program' in draft:
                        print(f"DEBUG: Found weekly_program in draft dict")
                        return draft['weekly_program']
                    print(f"DEBUG: Returning draft dict directly")
                    return draft

        print(f"DEBUG: Creating fallback empty program structure")
        return {"Day 1": [{"name": "No program data found", "sets": 0, "reps": "0", "target_rpe": 0, "rest": "N/A", "cues": "Please try generating a new program."}]}

    except Exception as e:
        print(f"ERROR parsing program: {e}")
        return {"Day 1": [{"name": "Error parsing program", "sets": 0, "reps": "0", "target_rpe": 0, "rest": "N/A", "cues": f"Error: {str(e)}"}]}

@app.route('/')
def index():
    """Display the current training program or generate a new one"""
    if 'program' not in session:
        return redirect(url_for('generate_program'))
    
    programs = session.get('all_programs', [])
    current_week = session.get('current_week', 1)
    
    return render_template('index.html', programs=programs, current_week=current_week)

@app.route('/generate', methods=['GET', 'POST'])
def generate_program():
    """Generate a new training program based on user input"""
    if request.method == 'POST':
        # Get user input
        user_input = request.form.get('user_input', '')
        persona = request.form.get('persona', '')
        
        # Handle empty input
        if not user_input.strip():
            user_input = "Generate a strength training program for the selected persona."
        
        # Update config (no critic_task_type needed)
        config = DEFAULT_CONFIG.copy()
        
        # Generate program
        program_input = user_input
        if persona:
            try:
                with open('Data/personas/personas_vers2.json') as f:
                    personas = json.load(f)["Personas"]
                selected_persona = personas.get(persona)
                if selected_persona:
                    program_input = f"{user_input}\nTarget Persona: {selected_persona}"
            except Exception as e:
                flash(f"Error loading persona: {e}")
        
        program_generator = get_program_generator(config)
        program_result = program_generator.create_program(user_input=program_input)
        
        # Parse and store the program in session
        parsed_program = parse_program(program_result.get('formatted'))
        session['program'] = parsed_program
        session['raw_program'] = program_result
        session['user_input'] = user_input
        session['persona'] = persona
        session['feedback'] = {}
        
        # Initialize week tracking
        session['current_week'] = 1
        session['all_programs'] = [{
            'week': 1,
            'program': parsed_program
        }]
        
        return redirect(url_for('index'))
    
    # Display form for initial program generation
    return render_template('generate.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Process user feedback for the current program"""
    if 'program' not in session:
        flash("No active program to provide feedback for.")
        return redirect(url_for('index'))
    feedback_data = {}
    program = session.get('program', {})

    for day, exercises in program.items():
        day_key = day.replace(' ', '')
        feedback_data[day] = []

        for i, exercise in enumerate(exercises):
            exercise_feedback = {
                'name': exercise['name'],
                'sets_data': [],
                'overall_feedback': request.form.get(f"{day_key}_ex{i}_feedback", "")
            }
            for j in range(exercise.get('sets', 0)):
                set_data = {
                    'weight': request.form.get(f"{day_key}_ex{i}_set{j}_weight"),
                    'reps': request.form.get(f"{day_key}_ex{i}_set{j}_reps"),
                    'actual_rpe': request.form.get(f"{day_key}_ex{i}_set{j}_actual_rpe")
                }
                exercise_feedback['sets_data'].append(set_data)

            feedback_data[day].append(exercise_feedback)

    session['feedback'] = feedback_data
    flash("Feedback submitted successfully!")
    return redirect(url_for('index'))

def create_next_week_prompt(user_input, current_program, feedback_data, current_week, persona=None):
    prompt = f"""
    Original User Input: {user_input}
    
    Previous Program: {json.dumps(current_program)}
    
    User Feedback: {json.dumps(feedback_data)}
    
    Please generate Week {current_week + 1} program considering the feedback provided.
    Autoregulate the training loads based on the actual performance data.
    """
    if persona:
        prompt += f"\nTarget Persona: {persona}"
    return prompt

@app.route('/next_week', methods=['GET', 'POST'])
def next_week():
    """Generate the next week's program based on feedback"""
    if 'program' not in session:
        flash("No program available to generate next week's program")
        return redirect(url_for('generate_program'))

    feedback_data = {}
    program = session.get('program', {})
    current_week = session.get('current_week', 1)

    for day, exercises in program.items():
        day_key = day.replace(' ', '')
        feedback_data[day] = []

        for i, exercise in enumerate(exercises):
            exercise_feedback = {
                'name': exercise['name'],
                'sets_data': [],
                'overall_feedback': request.form.get(f"{current_week}_{day_key}_ex{i}_feedback", "")
            }
            for j in range(exercise.get('sets', 0)):
                set_data = {
                    'weight': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_weight"),
                    'reps': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_reps"),
                    'actual_rpe': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_actual_rpe")
                }
                exercise_feedback['sets_data'].append(set_data)
            feedback_data[day].append(exercise_feedback)

    session['feedback'] = feedback_data
    current_program = session['raw_program']

    if 'formatted' in current_program and isinstance(current_program['formatted'], dict):
        if 'weekly_program' in current_program['formatted']:
            # Ensure our raw_program also has the weekly_program for easier access
            if not isinstance(current_program, dict):
                current_program = {}
            if 'weekly_program' not in current_program:
                current_program['weekly_program'] = current_program['formatted']['weekly_program']
    
    # Store the original week 1 program structure if moving to week 2
    current_week = session.get('current_week', 1)
    if current_week == 1:
        session['original_program_structure'] = session['program']

    current_program['week_number'] = current_week
    current_program['feedback'] = feedback_data

    next_week_input = create_next_week_prompt(
        user_input=session.get('user_input', ''),
        current_program=current_program,
        feedback_data=feedback_data,
        current_week=current_week,
        persona=session.get('persona_data') if session.get('persona') else None
    )

    if session.get('persona'):
        try:
            with open('Data/personas/personas_vers2.json') as f:
                personas = json.load(f)["Personas"]
            selected_persona = personas.get(session['persona'])
            if selected_persona:
                next_week_input += f"\nTarget Persona: {selected_persona}"
        except Exception as e:
            flash(f"Error loading persona: {e}")

    new_week = current_week + 1
    config = DEFAULT_CONFIG.copy()
    config['critic_prompt_settings'] = 'week2plus'  # Use week2plus for any week after week 1
    config['week_number'] = new_week  # Add week number to config
    
    # Generate next week's program
    program_generator = get_program_generator(config)
    program_result = program_generator.create_program(user_input=next_week_input)

    if new_week > 1 and 'original_program_structure' in session:
        original_structure = session['original_program_structure']
        new_program = parse_program(program_result.get('formatted'))

        merged_program = {}
        for day, exercises in original_structure.items():
            merged_program[day] = []
            for i, exercise in enumerate(exercises):
                preserved_exercise = exercise.copy()
                if day in new_program and i < len(new_program[day]):
                    new_exercise = new_program[day][i]
                    preserved_exercise['suggestion'] = new_exercise.get('suggestion', new_exercise.get('AI Progression'))
                merged_program[day].append(preserved_exercise)

        parsed_program = merged_program
    else:
        parsed_program = parse_program(program_result.get('formatted'))

    session['program'] = parsed_program
    session['raw_program'] = program_result
    session['feedback'] = {}
    session['current_week'] = new_week

    all_programs = session.get('all_programs', [])
    all_programs.append({'week': new_week, 'program': parsed_program})
    session['all_programs'] = all_programs

    flash(f"Week {new_week} program generated successfully!")
    return redirect(url_for('index'))

# Ensure the SavedPrograms directory exists
SAVED_PROGRAMS_DIR = os.path.join('Data', 'SavedPrograms')
os.makedirs(SAVED_PROGRAMS_DIR, exist_ok=True)

@app.route('/save_program', methods=['POST'])
def save_program():
    """Save the current program to a file"""
    if 'program' not in session:
        return jsonify({'success': False, 'message': 'No active program to save'})
    
    try:
        # Get program name from form
        program_name = request.form.get('program_name', '')
        
        # If no name provided, generate one based on date
        if not program_name:
            program_name = f"Program_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Make program name safe for filenames
        safe_name = "".join(c for c in program_name if c.isalnum() or c in [' ', '_', '-']).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Generate unique filename
        filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.json"
        filepath = os.path.join(SAVED_PROGRAMS_DIR, filename)
        
        # Prepare data to save
        save_data = {
            'program_name': program_name,
            'date_saved': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_input': session.get('user_input', ''),
            'persona': session.get('persona', ''),
            'current_week': session.get('current_week', 1),
            'raw_program': session.get('raw_program', {}),
            'all_programs': session.get('all_programs', []),
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': f'Program saved as {program_name}'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error saving program: {str(e)}'})

@app.route('/list_saved_programs', methods=['GET'])
def list_saved_programs():
    """List all saved programs"""
    try:
        programs = []
        for filename in os.listdir(SAVED_PROGRAMS_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(SAVED_PROGRAMS_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        programs.append({
                            'filename': filename,
                            'name': data.get('program_name', filename),
                            'date': data.get('date_saved', ''),
                            'weeks': len(data.get('all_programs', [])),
                            'current_week': data.get('current_week', 1)
                        })
                except Exception as e:
                    print(f"Error reading program file {filename}: {e}")
        programs.sort(key=lambda x: x.get('date', ''), reverse=True)
        return jsonify({'success': True, 'programs': programs})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error listing programs: {str(e)}'})

@app.route('/load_program', methods=['POST'])
def load_program():
    """Load a saved program"""
    try:
        filename = request.form.get('filename')
        if not filename:
            return jsonify({'success': False, 'message': 'No program selected'})
        
        filepath = os.path.join(SAVED_PROGRAMS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'Program file not found'})
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Restore session data
        session['program'] = data.get('all_programs', [])[-1].get('program', {}) if data.get('all_programs') else {}
        session['raw_program'] = data.get('raw_program', {})
        session['user_input'] = data.get('user_input', '')
        session['persona'] = data.get('persona', '')
        session['current_week'] = data.get('current_week', 1)
        session['all_programs'] = data.get('all_programs', [])
        session['feedback'] = {}
        
        return jsonify({'success': True, 'redirect': url_for('index')})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading program: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
