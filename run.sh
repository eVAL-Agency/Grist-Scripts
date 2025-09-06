#!/bin/bash

if [ ! -e ".venv" ]; then
	python3 -m venv ./.venv
	source .venv/bin/activate
    python3 -m pip install --upgrade pip
    pip3 install -e .
fi

source .venv/bin/activate

if [ $# -ge 2 -a "$1" == "--dev" ]; then
	flask run
else
	gunicorn -w 4 -b '127.0.0.1:5000' 'app:app'
fi