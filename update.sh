#!/bin/bash

if [ ! -e ".venv" ]; then
	python3 -m venv ./.venv
fi
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip3 install -e .