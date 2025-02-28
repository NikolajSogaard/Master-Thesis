import os
import sys
import json

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from agent_system import (
    setup_llm,
    ProgramGenerator,
    Writer,
    Critic,
    Editor,
    RagRetriever,
)

from prompts import (
    WriterPromptSettings,
    CriticPromptSettings,
    WRITER_PROMPT_SETTINGS,
    CRITIC_PROMPT_SETTINGS,
)

def test_full_pipeline():
    """Test the entire pipeline with RAG integration"""
    print("Setting up RAG retriever...")
    retriever = RagRetriever(top_k=3)
    
    print("Setting up LLM models...")
    llm_writer = setup_llm(model="gemini-2.0-flash", respond_as_json=True)
    llm_critic = setup_llm(model="gemini-2.0-flash", respond_as_json=False)
    
    print("Setting up agents...")
    writer = Writer(
        model=llm_writer,
        role=WRITER_PROMPT_SETTINGS['v1'].role,
        structure=WRITER_PROMPT_SETTINGS['v1'].structure,
        task=WRITER_PROMPT_SETTINGS['v1'].task,
        task_revision=WRITER_PROMPT_SETTINGS['v1'].task_revision,
        retriever=retriever,
    )
    critic = Critic(
        model=llm_critic,
        role=CRITIC_PROMPT_SETTINGS['v1'].role,
        task=CRITIC_PROMPT_SETTINGS['v1'].task,
        retriever=retriever,
    )
    editor = Editor()
    
    print("Setting up program generator...")
    program_generator = ProgramGenerator(writer=writer, critic=critic, editor=editor)
    
    # Test inputs
    test_inputs = [
        "Create a strength training program for a beginner",
        "I want a bodybuilding program that focuses on aesthetics"
    ]
    
    # Process each test input
    for i, test_input in enumerate(test_inputs):
        print(f"\n\n--- Testing Input {i+1}: {test_input} ---\n")
        program = program_generator.create_program(user_input=test_input)
        
        # Save the result for inspection
        output_file = f"test_output_{i+1}.json"
        with open(output_file, 'w') as f:
            json.dump(program, f, indent=2)
        print(f"Program generated and saved to {output_file}")
        
        # Print summary
        print(f"Program required {program.get('iterations', 0)} iteration(s)")
        if program.get('feedback'):
            print("Final feedback:", program['feedback'][:100] + "...")
        else:
            print("Program was accepted without further feedback")

if __name__ == "__main__":
    test_full_pipeline()
