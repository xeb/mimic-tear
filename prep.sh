#!/bin/bash
source venv/local/bin/activate
#python create_data.py
openai tools fine_tunes.prepare_data -f ../goofyspot_history2/prompt_completion.jsonl
