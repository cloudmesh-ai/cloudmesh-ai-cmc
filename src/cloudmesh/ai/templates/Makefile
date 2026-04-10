# Variables
PYTHON := python
PIP := pip
{name}_DIR := cme-{name}
EXT_DIR := cme-extension-example

# Detect Shell and Config File
CURRENT_SHELL := $(shell echo $$SHELL | awk -F/ '{print $$NF}')
ifeq ($(CURRENT_SHELL),zsh)
    SHELL_CONFIG := $(HOME)/.zshrc
    COMP_CMD := eval "$$(_CME_COMPLETE=zsh_source cme)"
else ifeq ($(CURRENT_SHELL),fish)
    SHELL_CONFIG := $(HOME)/.config/fish/config.fish
    COMP_CMD := _CME_COMPLETE=fish_source cme | source
else
    SHELL_CONFIG := $(HOME)/.bashrc
    COMP_CMD := eval "$$(_CME_COMPLETE=bash_source cme)"
endif

.PHONY: help install install-ext clean reset-registry list setup-shell manual-md manual-txt manual-qmd

help:
	@echo "CME Development Management"
	@echo "--------------------------"
	@echo "install          Install cme {name} in editable mode"
	@echo "install-ext      Install the example extension in editable mode"
	@echo "clean            Remove build artifacts and __pycache__"
	@echo "reset-registry   Delete the ~/.cme_registry.json file"
	@echo "list             List currently registered cme commands"
	@echo "setup-shell      Detect shell and configure autocompletion"

install:
	cd $({name}_DIR) && $(PIP) install -e .

install-ext:
	cd $(EXT_DIR) && $(PIP) install -e .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

reset-registry:
	rm -f $(HOME)/.cme_registry.json
	@echo "Registry reset."

list:
	cme command list

setup-shell:
	@echo "Detected shell: $(CURRENT_SHELL)"
	@echo "Target config: $(SHELL_CONFIG)"
	@grep -q "_CME_COMPLETE" $(SHELL_CONFIG) 2>/dev/null || \
		echo '\n# CME autocompletion\n$(COMP_CMD)' >> $(SHELL_CONFIG)
	@echo "Success. Please run 'source $(SHELL_CONFIG)' or restart your terminal."

]