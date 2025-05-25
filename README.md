# Master-Thesis: AI Strength Program Generator

This project uses AI agents, including Large Language Models (LLMs) and Retrieval Augmented Generation (RAG), to create personalized strength training programs.

## Setup
### 1. API Key Configuration
This project uses Google Gemini for its AI capabilities. You'll need an API key.

**Get your API Key:**
You'll need a Google Gemini API key.
**Configure the Key:**
    1.  Create a file named `cre.env` in the main project directory and add your API key.
    2.  Inside `cre.env`, add your API key like this:
    *   The file `agent_system/setup_api.py` is responsible for loading this key to allow the AI models to work.

### 2. Build Your Own Knowledge Database (for RAG)
The system uses Retrieval Augmented Generation (RAG) to provide the AI with relevant information from strength training literature. This information is stored in a local vector database.

**Add PDF Documents:**
Place your strength training PDF books or documents into the `Data/books/` folder.
**Build the Database:**
Run script (`build_db.py`) to read the PDFs from `Data/books/`.
The embeddings will be stored in a local vector database (ChromaDB) located at `data/chroma_db/`.

## How the System Works 
The project uses a Flask web app (`app.py`) and a team of AI agents to create strength programs.

*   **`app.py` (Web App):** Handles user interaction, manages program generation requests, and displays results.
    *   For testing purposes, the system can utilize predefined user personas. These personas are defined in `Data/personas/personas_vers2.json` and can be selected in the web interface to simulate different user types.
*   **`agent_system/setup_api.py`:** Connects to Google Gemini AI models using your API key from `cre.env`.
*   **`build_db.py` & `rag_retrieval.py` (Knowledge Base - RAG):**
    *   `build_db.py`: Processes PDFs in `Data/books/` into a searchable ChromaDB vector database (`data/chroma_db/`).
    *   `rag_retrieval.py`: Allows AI agents to search this database for relevant strength training information to improve their responses.
*   **`agent_system/generator.py` (`ProgramGenerator`):** Manages the AI agent team (Writer, Critic, Editor) using LangGraph to define their workflow.
*   **`agent_system/agents/` (AI Agent Team):**
    *   **`writer.py` (Writer):** Generates the initial program draft and revises it based on feedback or for weekly progression. Uses RAG for knowledge.
    *   **`critic.py` (Critic):** Evaluates the Writer's draft against several criteria (frequency, exercise selection, volume, RPE, progression). Uses RAG for informed critiques.
    *   **`editor.py` (Editor):** Clean JSON structure for the web app.
*   **`prompts/` (Agent Instructions):** Contains detailed Python files (`writer_prompts.py`, `critic_prompts.py`) that define the roles, tasks, and desired output formats for the AI agents.

