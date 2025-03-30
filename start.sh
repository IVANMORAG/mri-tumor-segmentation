#!/bin/bash
python -m gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:$PORT --worker-class=gthread --threads=2 app:app