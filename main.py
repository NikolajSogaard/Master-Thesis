import argparse

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    # User settings
    parser.add_argument('--mode', type=str, default='new', choices=['new', 'revise']) # TODO only implemented a "new" version, could add control flow logic to handle the revise case, probably with a slightly modified agent framework..?
    parser.add_argument('--user-input', type=str, help='Some instructions') # TODO probably want to pass this as an fname or smth

    # Data settings
    ...

    # Model/LLM/API settings
    parser.add_argument('--model', type=str, default='gemini-2.0-flash')
    parser.add_argument('--max-tokens', type=int, default=2048)
    parser.add_argument('--writer-temperature', type=float, default=0.6)
    parser.add_argument('--writer-top-p', type=float, default=0.9)

    # Prompt info
    parser.add_argument('--writer-prompt-settings', type=str, default='v1', choices=WRITER_PROMPT_SETTINGS.keys())
    parser.add_argument('--critic-prompt-settings', type=str, default='v1', choices=CRITIC_PROMPT_SETTINGS.keys())

    args = parser.parse_args()

    return args


def setup_agents(
        args: argparse.Namespace,
        writer_prompt_settings: WriterPromptSettings,
        critic_prompt_settings: CriticPromptSettings,
        ) -> ProgramGenerator:
    # Underlying LLMs
    llm_writer = setup_llm(
        model=args.model,
        respond_as_json=True,
        temperature=args.writer_temperature,
        top_p=args.writer_top_p,
    )
    llm_critic = setup_llm(
        model=args.model,
        max_tokens=args.max_tokens,
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
    robot_article_agent = ProgramGenerator(
        writer=writer,
        critic=critic,
        editor=editor,
    )

    return robot_article_agent


def main():
    args = parse_args()

    # Setup prompt settings
    writer_prompt_settings = WRITER_PROMPT_SETTINGS[args.writer_prompt_settings]
    critic_prompt_settings = CRITIC_PROMPT_SETTINGS[args.critic_prompt_settings]

    # Load data
    ...

    # Setup agents
    program_generator = setup_agents(
        args=args,
        writer_prompt_settings=writer_prompt_settings,
        critic_prompt_settings=critic_prompt_settings,
    )

    # Create program
    program = program_generator.create_program(
        user_input=args.user_input,
    )
    print(program) # FIXME proper logging

    # Save program
    ...


if __name__ == '__main__':
    main()
