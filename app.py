"""
This file should be the new main file insteed of main.py.
This is to get the output as a web application. 
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_session import Session  # Import Flask-Session extension
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

# Removed MultiCritic import as it's no longer needed

from rag_retrieval import retrieve_and_generate

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Configure server-side sessions to avoid cookie size limit issues
app.config["SESSION_TYPE"] = "filesystem"  # Store sessions on filesystem instead of cookies
app.config["SESSION_FILE_DIR"] = os.path.join(tempfile.gettempdir(), "flask_session_files")
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=24)  # Session timeout
app.config["SESSION_USE_SIGNER"] = True  # Sign the session cookie
Session(app)  # Initialize Flask-Session

# Default configuration
DEFAULT_CONFIG = {
    'model': 'gemini-2.0-flash',
    'max_tokens': 2048,
    'writer_temperature': 0.6,
    'writer_top_p': 0.9,
    'writer_prompt_settings': 'v1',
    'critic_prompt_settings': 'week1',
    'max_iterations': 4
}

def get_program_generator(config=None):
    """Setup the program generator with the given or default config"""
    if config is None:
        config = DEFAULT_CONFIG
    
    # Setup prompt settings based on week/task
    week_number = config.get('week_number', 1)
    
    # Select writer prompt settings based on week/task
    writer_type = "initial"  # Default for initial program
    
    if week_number > 1:
        writer_type = "progression"  # Use progression for week 2+
    elif config.get('is_revision', False):
        writer_type = "revision"  # Use revision for critique-based revisions
        
    writer_prompt_settings = WRITER_PROMPT_SETTINGS[writer_type]
    
    # Use week-specific critic settings
    critic_setting_key = 'week2plus' if week_number > 1 else 'week1'
    critic_prompt_settings = CRITIC_PROMPT_SETTINGS[critic_setting_key]
    
    # Underlying LLMs
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
    
    # Agents
    writer = Writer(
        model=llm_writer,
        role=writer_prompt_settings.role,
        structure=writer_prompt_settings.structure,
        task=writer_prompt_settings.task,
        task_revision=writer_prompt_settings.task_revision,
        writer_type=writer_type,  # Pass the writer type
        retrieval_fn=retrieve_and_generate  # Add retrieval function
    )
    
    critic = Critic(
        model=llm_critic,
        role=critic_prompt_settings.role,
        tasks=getattr(critic_prompt_settings, 'tasks', None),  # Only tasks are provided now
        retrieval_fn=retrieve_and_generate
    )
    
    editor = Editor()
    
    # Coordinator
    return ProgramGenerator(
        writer=writer,
        critic=critic,
        editor=editor,
        max_iterations=config.get('max_iterations', 2)  # Get max_iterations from config
    )

def parse_program(program_output):
    """Parse the program output into a structured format for the template"""
    try:
        # Parse JSON if it's a string
        if isinstance(program_output, str):
            program_output = json.loads(program_output)
        
        # Extract the weekly program structure
        if isinstance(program_output, dict):
            if 'weekly_program' in program_output:
                return program_output['weekly_program']
            elif 'formatted' in program_output:
                formatted = program_output['formatted']
                if isinstance(formatted, str):
                    try:
                        return json.loads(formatted)['weekly_program']
                    except (json.JSONDecodeError, KeyError):
                        pass
                elif isinstance(formatted, dict) and 'weekly_program' in formatted:
                    return formatted['weekly_program']
                return formatted
        
        # If we get here, try to use the program as-is
        return program_output
    except Exception as e:
        print(f"Error parsing program: {e}")
        # Return a default empty program structure if parsing fails
        return {}

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
        
        # No longer need to get critic_task_type from the form
        
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
    
    # Collect feedback data
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
            
            # Get the number of sets correctly - it's already an integer
            sets_count = exercise.get('sets', 0)
            
            # Process each set's feedback
            for j in range(sets_count):
                set_data = {
                    'weight': request.form.get(f"{day_key}_ex{i}_set{j}_weight"),
                    'reps': request.form.get(f"{day_key}_ex{i}_set{j}_reps"),
                    'actual_rpe': request.form.get(f"{day_key}_ex{i}_set{j}_actual_rpe")
                }
                exercise_feedback['sets_data'].append(set_data)
            
            feedback_data[day].append(exercise_feedback)
    
    # Store feedback in session
    session['feedback'] = feedback_data
    
    flash("Feedback submitted successfully!")
    return redirect(url_for('index'))

# Simplified helper function that doesn't specify field details since they're in the prompt structure
def create_next_week_prompt(user_input, current_program, feedback_data, current_week, persona=None):
    """Creates the prompt for generating the next week's program"""
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
    
    # First, collect feedback data for the current week
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
            
            # Get the number of sets correctly - it's already an integer
            sets_count = exercise.get('sets', 0)
            
            # Process each set's feedback
            for j in range(sets_count):
                set_data = {
                    'weight': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_weight"),
                    'reps': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_reps"),
                    'actual_rpe': request.form.get(f"{current_week}_{day_key}_ex{i}_set{j}_actual_rpe")
                }
                exercise_feedback['sets_data'].append(set_data)
            
            feedback_data[day].append(exercise_feedback)
    
    # Store feedback in session
    session['feedback'] = feedback_data
    
    # Prepare input for next week's program
    current_program = session['raw_program']
    
    # Use the helper function to create the prompt
    next_week_input = create_next_week_prompt(
        user_input=session.get('user_input', ''),
        current_program=session['raw_program'],
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
    
    # Update config for next week's program with week number
    new_week = current_week + 1
    config = DEFAULT_CONFIG.copy()
    config['critic_prompt_settings'] = 'week2plus'  # Use week2plus for any week after week 1
    config['week_number'] = new_week  # Add week number to config
    
    # Generate next week's program
    program_generator = get_program_generator(config)
    program_result = program_generator.create_program(user_input=next_week_input)
    
    # Update session with new program
    parsed_program = parse_program(program_result.get('formatted'))
    session['program'] = parsed_program
    session['raw_program'] = program_result
    session['feedback'] = {}
    
    # Increment week number and add to programs list
    new_week = current_week + 1
    session['current_week'] = new_week
    
    all_programs = session.get('all_programs', [])
    all_programs.append({
        'week': new_week,
        'program': parsed_program
    })
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
        
        # Sort by date (most recent first)
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
