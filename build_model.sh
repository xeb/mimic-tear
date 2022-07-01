#!/bin/bash
openai api fine_tunes.create -t "../goofyspot_history/dan_history.jsonl" -m "ada"
openai api fine_tunes.list