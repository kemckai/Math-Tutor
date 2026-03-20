# Math Tutor

An interactive, AI-powered math tutoring application built with Streamlit. Practice math concepts step-by-step, draw solutions on a canvas, and get intelligent hints powered by OpenAI.

## Live App

- Deploy the Streamlit app on Streamlit Community Cloud for the actual interactive experience.
- Use GitHub Pages only as a lightweight landing page.

## Features

- **Concept Library** — Browse and select math topics organized by category
- **Problem Generator** — AI-generated problems tailored to the selected concept
- **Step Validator** — Real-time feedback as you work through each problem step
- **Hint System** — Contextual hints that guide without giving away the answer
- **Drawable Canvas** — Write or draw solutions by hand using OCR recognition
- **Progress Tracking** — Mastery levels and attempt history stored in a local database
- **Prerequisite Mapping** — Concepts unlock based on what you've already mastered

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI framework
- [OpenAI](https://platform.openai.com/) — Problem generation and hint system
- [SymPy](https://www.sympy.org/) — Symbolic math validation
- [SQLAlchemy](https://www.sqlalchemy.org/) — Local SQLite database
- [streamlit-drawable-canvas](https://github.com/andfanilo/streamlit-drawable-canvas) — Handwriting input
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — Handwriting recognition

## Setup

### Prerequisites

- Python 3.9+
- [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) installed on your system

### Install

```bash
git clone https://github.com/kemckai/Math-Tutor.git
cd Math-Tutor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Run

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

## Deploy

### Streamlit Community Cloud

This repo is set up for Streamlit Community Cloud deployment:

- `app.py` is the entrypoint
- `requirements.txt` contains Python dependencies
- `packages.txt` contains system packages for OCR
- `.streamlit/config.toml` contains Streamlit app settings

Deployment steps:

1. Go to Streamlit Community Cloud.
2. Connect the GitHub repo `kemckai/Math-Tutor`.
3. Select `app.py` as the main file.
4. Add `OPENAI_API_KEY` in the app secrets/settings.
5. Deploy.

### GitHub Pages

GitHub Pages cannot run a Python Streamlit app. In this repo it is intended only for a simple landing page via `index.html`.

## Project Structure

```
├── app.py                  # Main Streamlit app
├── config.py               # Settings and environment config
├── logger.py               # Logging setup
├── concepts/
│   ├── concept_library.py  # Math concept definitions
│   └── prerequisites.py    # Prerequisite graph
├── database/
│   ├── db_manager.py       # Database operations
│   └── models.py           # SQLAlchemy models
├── recognition/
│   ├── canvas_handler.py   # Drawable canvas integration
│   └── ocr_processor.py    # Tesseract OCR processing
├── tutor/
│   ├── problem_generator.py # AI problem generation
│   ├── step_validator.py    # Step-by-step validation
│   └── hint_system.py       # Hint generation
└── utils/
    ├── math_helpers.py      # Math utility functions
    └── session_manager.py   # Streamlit session state
```
