#!/bin/bash
gunicorn --workers 4 --timeout 300 --bind 0.0.0.0:10000 app:app