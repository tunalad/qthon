PACKAGE_NAME = qthon
BINARY_NAME = $(PACKAGE_NAME)
INSTALL_DIR = $(HOME)/.local/bin
VENV_DIR = make_venv
PYTHON = python3

# List all icons manually or use find to gather them
ASSETS_ICONS = $(shell find assets/fugue-icons -type f)
ASSETS_UI = $(shell find assets/ui -type f)
ASSETS_UTILS = $(shell find assets/utils -type f)
ASSETS_WINDOWS = $(shell find assets/windows -type f)

all: build

build: venv
	$(VENV_DIR)/bin/pyinstaller qthon.spec

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/python -m pip install pyinstaller
	$(VENV_DIR)/bin/python -m pip install -r requirements.txt

install: build
	install -m 755 dist/$(BINARY_NAME) $(INSTALL_DIR)/$(BINARY_NAME)

uninstall:
	rm -f $(INSTALL_DIR)/$(BINARY_NAME)

clean:
	rm -rf build dist $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +

lean:
	@echo -e "\e[1;35m💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜\e[0m"
	@echo -e "\e[1;35m💜💜💜💜💜💜💜💜I LOVE LEAN!!!💜💜💜💜💜💜💜💜💜\e[0m"
	@echo -e "\e[1;35m💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜\e[0m"
	@echo -e "\e[1;35m💜I'M ON 'EM BEANS FOR REAL (YEH, YEAH, YEAH)💜\e[0m"
	@echo -e "\e[1;35m💜I'M ON THE LEAN FOR REAL (WHAT? YEAH, YEAH)💜\e[0m"
	@echo -e "\e[1;35m💜I'M ON 'EM BEANS FOR REAL (YEA, YEAH, YEAH)💜\e[0m"
	@echo -e "\e[1;35m💜💜💜I'M ON THE LEAN FOR REAL (YEAH-YEAH)💜💜💜\e[0m"
	@echo -e "\e[1;35m💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜💜\e[0m"
	@exit 1

.PHONY: all build install uninstall clean lean venv
