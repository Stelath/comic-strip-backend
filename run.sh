#!/bin/bash

# export FLASK_RUN_PORT=3000

# flask --app comic_strip_backend.py run
gunicorn -w 4 -b 0.0.0.0:8080 comic_strip_backend:app
