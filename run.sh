#!/bin/bash

venv_dir=venv
if [ ! -d $venv_dir ]; then
  echo "Virtual environment not found. Setting up virtual environment under $venv_dir"
  python3 -m venv $venv_dir
  source $venv_dir/bin/activate
  pip install -r requirements.txt
fi
source $venv_dir/bin/activate
export PYTHONPATH=$PYTHONPATH:./

python3 main.py
