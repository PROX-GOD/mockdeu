# MockDeu - Advanced Visa Interview Simulator
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/PROX-GOD/mockdeu)

MockDeu is a state-of-the-art, open-source AI simulator designed to prepare applicants for F-1 (Student) and B1/B2 (Business/Tourism) visa interviews. It leverages advanced Large Language Models (LLMs), real-time Speech-to-Text (STT), and Text-to-Speech (TTS) to create a realistic and immersive interview experience.

## Features

-   **Dual Interface**: Choose between a robust **CLI** or a premium **GUI** with an "Embassy" theme.
-   **Realistic AI Officer**: Simulates various officer personas (Strict, Skeptical, Friendly) and embassy contexts.
-   **Dual Visa Support**: Specialized training for F-1 and B1/B2 visa categories.
-   **Real-time Interaction**: Low-latency voice interaction using AssemblyAI and optimized TTS.
-   **Detailed Feedback**: Comprehensive post-interview analysis with critiques and improvement suggestions.
-   **Secure & Modular**: Built with security best practices and a modular architecture.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/prox-god/mockdeu.git
    cd mockdeu
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure API Keys:
    - Copy `.env.example` to `.env`.
    - Add your `OPENROUTER_KEY` and `ASSEMBLYAI_API_KEY`.

## Usage

Run the simulator from the project root:

```bash
python -m mockdeu.main
```

Follow the on-screen prompts to select your interface (CLI/GUI), visa type, officer style, and embassy context.

## Project Structure

-   `mockdeu/core/`: Core services (STT, TTS, LLM).
-   `mockdeu/logic/`: Business logic (Interview flow, Scoring, DS-160).
-   `mockdeu/interfaces/`: UI implementations (CLI, GUI).
-   `mockdeu/data/`: Static data and configurations.
-   `cases/`: Stores interview transcripts and feedback reports.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
