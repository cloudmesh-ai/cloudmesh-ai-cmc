# Variables
PYTHON := python
PIP := pip
NAME := {name}

.PHONY: help install clean list

help:
	@echo "CMC Command Development Management"
	@echo "----------------------------------"
	@echo "install          Install the command in editable mode"
	@echo "clean            Remove build artifacts and __pycache__"
	@echo "list             List currently registered cmc commands"

install:
	$(PIP) install -e .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {{}} +
	find . -type d -name "*.egg-info" -exec rm -rf {{}} +
	find . -type d -name "build" -exec rm -rf {{}} +
	find . -type d -name "dist" -exec rm -rf {{}} +

list:
	cmc command list