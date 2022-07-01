#!/bin/bash
source venv/bin/activate
python create_data.py
openai tools fine_tunes.prepare_data -f ../goofyspot_history/dan_history.jsonl