# Bedrock Dentist SOAP Agent

This repository contains a simple rule-based "meeting transcription agent" for
dental SOAP note charting. The agent expects a text transcript of a
conversation (for example, a short stand-up between a dentist and a dental
assistant while treating a patient) and produces a structured Subjective,
Objective, Assessment, and Plan summary.

## Quick start

1. Create and activate a Python 3.9+ virtual environment.
2. Install the project in editable mode with the optional CLI extras:

   ```bash
   pip install -e .[cli]
   ```

3. Run the agent against one of the sample transcripts:

   ```bash
   python -m dentist_agent.transcription_agent transcripts/sample_transcript.txt
   ```

The agent will print the generated SOAP note to standard output as formatted
Markdown.

## Project layout

```
├── dentist_agent/
│   ├── __init__.py
│   └── transcription_agent.py
├── transcripts/
│   └── sample_transcript.txt
├── tests/
│   └── test_transcription_agent.py
├── README.md
└── pyproject.toml
```

* `dentist_agent/transcription_agent.py` implements the rule-based
  summarisation logic.
* `transcripts/sample_transcript.txt` provides a short example conversation.
* `tests/test_transcription_agent.py` exercises the core extraction helper.

Run the automated checks with:

```bash
python -m pytest
```
