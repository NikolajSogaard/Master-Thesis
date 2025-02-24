from langgraph.graph import Graph

from .agents import (
    Writer,
    Critic,
    Editor,
)


class ProgramGenerator:
    def __init__(
            self,
            writer: Writer,
            critic: Critic,
            editor: Editor,
            ):
        # Agents
        self.writer = writer
        self.critic = critic
        self.editor = editor

        # Build graph
        graph = Graph()

        # Agent nodes
        graph.add_node('writer', self.writer)
        graph.add_node('critic', self.critic)

        # Arcs
        graph.add_edge(
            start_key='writer',
            end_key='critic',
        )
        graph.add_conditional_edges(
            source='critic',
            path=self.provide_critique,
            path_map={
                'accept': 'editor',
                'revise': 'writer',
            },
        )

        # Set start and end node
        graph.set_entry_point('writer')
        graph.set_finish_point('editor')

        self.app = graph.compile()

    def provide_critique(self, program: dict[str, str | None]) -> str:
        if program['feedback'] is None:
            return 'accept'

        return 'revise'

    def create_program(
            self,
            user_input: str,
            ) -> dict[str, str | None]:
        # Prepare inputs
        program = {
            'user-input': user_input,
            # Maybe you add other information...
        }

        final_state = self.app.invoke(program)

        return final_state
