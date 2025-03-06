"""
This file should be the new main file insteed of main.py.
This is to get the output as a web application. 


"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
import argparse
from datetime import datetime

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

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Default configuration
DEFAULT_CONFIG = {
    'model': 'gemini-2.0-flash',
    'max_tokens': 2048,
    'writer_temperature': 0.6,
    'writer_top_p': 0.9,
    'writer_prompt_settings': 'v1',
    'critic_prompt_settings': 'v1'
}

def get_program_generator(config=None):
    """Setup the program generator with the given or default config"""
    if config is None:
        config = DEFAULT_CONFIG
    
    # Setup prompt settings
    writer_prompt_settings = WRITER_PROMPT_SETTINGS[config['writer_prompt_settings']]
    critic_prompt_settings = CRITIC_PROMPT_SETTINGS[config['critic_prompt_settings']]
    
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
    )
    critic = Critic(
        model=llm_critic,
        role=critic_prompt_settings.role,
        task=critic_prompt_settings.task,
    )
    
    editor = Editor()
    
    # Coordinator
    return ProgramGenerator(
        writer=writer,
        critic=critic,
        editor=editor,
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
    
    return render_template('index.html', program=session['program'])

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
        
        program_generator = get_program_generator()
        program_result = program_generator.create_program(user_input=program_input)
        
        # Parse and store the program in session
        session['program'] = parse_program(program_result.get('formatted'))
        session['raw_program'] = program_result
        session['user_input'] = user_input
        session['persona'] = persona
        session['feedback'] = {}
        
        return redirect(url_for('index'))
    
    # Display form for initial program generation
    return render_template('generate.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Process user feedback for the current program"""
    if 'program' not in session:
        flash("No active program to provide feedback for.")
        return redirect(url_for('index'))
    
    # Collect feedback from form
    feedback = {}
    for day, exercises in session['program'].items():
        day_key = day.replace(' ', '')
        feedback[day] = []
        
        for i, _ in enumerate(exercises):
            exercise_feedback = {
                'name': request.form.get(f"{day_key}_ex{i}_name", ""),
                'sets': []
            }
            
            # Get all set data for this exercise
            sets_count = len(exercises[i].get('sets', 0))
            for set_num in range(sets_count):
                set_data = {
                    'weight': request.form.get(f"{day_key}_ex{i}_set{set_num}_weight", ""),
                    'reps': request.form.get(f"{day_key}_ex{i}_set{set_num}_reps", ""),
                    'actual_rpe': request.form.get(f"{day_key}_ex{i}_set{set_num}_actual_rpe", "")
                }
                exercise_feedback['sets'].append(set_data)
            
            # Get overall exercise feedback
            exercise_feedback['overall'] = request.form.get(f"{day_key}_ex{i}_feedback", "")
            feedback[day].append(exercise_feedback)
    
    # Store feedback in session
    session['feedback'] = feedback
    flash("Feedback submitted successfully!")
    return redirect(url_for('index'))

@app.route('/next_week')
def next_week():
    """Generate the next week's program based on feedback"""
    if 'program' not in session or 'feedback' not in session:
        flash("No program or feedback available to generate next week's program")
        return redirect(url_for('generate_program'))
    
    # Prepare input for next week's program
    current_program = session['raw_program']
    feedback = session['feedback']
    
    # Create input that includes previous program and feedback
    next_week_input = f"""
    Original User Input: {session.get('user_input', '')}
    
    Previous Program: {json.dumps(current_program)}
    
    User Feedback: {json.dumps(feedback)}
    
    Please generate the next week's program considering the feedback provided.
    Autoregulate the training loads based on the actual performance data.
    """
    
    if session.get('persona'):
        try:
            with open('Data/personas/personas_vers2.json') as f:
                personas = json.load(f)["Personas"]
            selected_persona = personas.get(session['persona'])
            if selected_persona:
                next_week_input += f"\nTarget Persona: {selected_persona}"
        except Exception as e:
            flash(f"Error loading persona: {e}")
    
    # Generate next week's program
    program_generator = get_program_generator()
    program_result = program_generator.create_program(user_input=next_week_input)
    
    # Update session with new program
    session['program'] = parse_program(program_result.get('formatted'))
    session['raw_program'] = program_result
    session['feedback'] = {}
    
    flash("Next week's program generated successfully!")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
