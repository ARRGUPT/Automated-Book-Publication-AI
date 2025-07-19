# Internship Assignment: Automated Book Publication Workflow

This project implements a prototype for an Automated Book Publication Workflow, leveraging AI (Large Language Models) for content generation and review, web scraping, and a human-in-the-loop system for refinement. The system demonstrates the core capabilities outlined in the assignment, with conceptual integration for Reinforcement Learning (RL) components.

## Objective

The primary objective is to create a system that can fetch content from a web URL, apply AI-driven "spinning" to chapters, and allow multiple human-in-the-loop iterations for review and finalization.

## Key Capabilities Implemented & Conceptualized

### 1. Scraping & Screenshots
- **Implemented:** Uses `Playwright` to navigate to a specified URL, extract the main textual content (paragraphs), and capture a full-page screenshot. Screenshots are saved to the `screenshots/` directory.
- **Conceptual RL Integration:** A successful scrape that yields a significant amount of relevant text (e.g., above a certain word count) would serve as a positive reward signal for an RL agent optimizing the scraping strategy (e.g., choosing optimal selectors, handling dynamic content). Conversely, failed scrapes or irrelevant content would yield negative rewards.

### 2. AI Writing & Review (LLMs)
- **Implemented:** Leverages the Google Gemini API (`gemini-pro`) to perform:
    - **Chapter "Spinning":** The AI Writer takes scraped content and rewrites it in a more engaging narrative style. Multiple iterations are supported in the workflow.
    - **AI Reviewer:** The AI Reviewer analyzes the AI-spun text for clarity, coherence, grammar, and engagement, providing constructive feedback.
- **Conceptual RL Integration:**
    - **AI Writer:** A "good" spun chapter (e.g., one that is accepted by the human reviewer, or scores high on an automated rubric for originality, length, and style adherence) would provide a positive reward to an RL agent training the AI Writer.
    - **AI Reviewer:** A review that is deemed "helpful" or "actionable" by human feedback or subsequent AI improvements could provide a positive reward for the AI Reviewer.

### 3. Human-in-the-Loop
- **Implemented:** A command-line interface allows the human user (acting as writer, reviewer, or editor) to:
    - View the AI-generated chapter.
    - `accept` the chapter (marks it as final).
    - `edit` the chapter (allows manual text input for corrections/improvements).
    - `reject` the chapter (indicates dissatisfaction).
- **Conceptual RL Inference:** Human decisions and edits are critical feedback signals.
    - `accept`: Strong positive reward, directly reinforcing the AI's generation quality for that specific input.
    - `edit`: Provides granular feedback; specific edits can be analyzed (e.g., using an LLM to identify the "type" of edit) to generate more nuanced rewards for the AI model, guiding future refinements.
    - `reject`: Strong negative reward, indicating the AI's output was far from desirable for that input. This feedback directly informs the RL agent to adjust its parameters.

### 4. Agentic API (Conceptualized for time constraints)
- **Implemented (Basic Flow):** The `main.py` script orchestrates a sequential flow between the "Scraping Agent," "AI Writer Agent," "AI Reviewer Agent," and the "Human Editor."
- **Conceptual Extensions:**
    - **Seamless Content Flow:** While currently sequential, a more robust Agentic API would involve message queues or pub/sub systems for asynchronous communication between specialized microservices (e.g., a dedicated service for scraping, another for LLM calls).
    - **Voice Support:** This could be integrated using Speech-to-Text (STT) for human input (e.g., dictating edits) and Text-to-Speech (TTS) for AI read-alouds of chapters or reviews. This would sit on top of the existing text-based workflow.
    - **Version Support:** Fully implemented using `ChromaDB` which stores each version (original, AI-spun iterations, human-edited, final) with unique IDs and metadata.
    - **Semantic Search:** Implemented using `ChromaDB` to perform searches based on the meaning of the query, retrieving relevant chapter versions regardless of exact keyword matches.
    - **RL Based Reward Model:** The feedback from human-in-the-loop and the performance metrics of each "agent" (scraper efficiency, AI writing quality) would feed into a centralized RL reward model. This model would then guide the learning process of each AI agent to continuously improve the entire workflow. For example, if an AI-spun chapter is frequently rejected for tone, the RL model would nudge the AI Writer to adjust its tone.

## Core Tools Used

- **Python:** The primary programming language for the entire project.
- **Playwright:** For web scraping and taking screenshots.
- **Google Gemini API (via `google-generativeai`):** For AI writing, reviewing, and editing tasks.
- **ChromaDB:** A vector database used for:
    - Content versioning (storing different stages/versions of chapters).
    - Semantic search (allowing retrieval of content based on meaning).
- **Conceptual RL Search Algorithm:** Explained how this would inform data retrieval based on learned rewards.

## Setup and Running Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ARRGUPT/Automated-Book-Publication-AI
    cd Automated-Book-Publication-AI
    ```
2.  **Set up Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows: venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    playwright install
    ```
4.  **Configure Gemini API Key:**
    Obtain your API key from [Google AI Studio](https://aistudio.google.com/).
    Set it as an environment variable before running the script:
    - **Linux/macOS:**
        ```bash
        export GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
    - **Windows (Command Prompt):**
        ```cmd
        set GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
    - **Windows (PowerShell):**
        ```powershell
        $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
    (Replace `YOUR_API_KEY_HERE` with your actual key.)
5.  **Run the Workflow:**
    ```bash
    python main.py
    ```
    The script will guide you through the human-in-the-loop iterations and demonstrate semantic search at the end.

## Submission Details

- **Recorded Video:** A demonstration video showcasing the workflow (scraping, AI spinning, human review, semantic search).
- **Public Git Repository:** This repository contains all the code and documentation.

## Developer License & Plagiarism Policy

- The developer retains their license to this code.
- This task is for evaluation purposes only.
- Plagiarism is strictly prohibited. All code and explanations were written by me. AI tools were used for generating content within the simulated workflow as per the assignment's requirements, but not for generating the submission itself.

## All the best!

---