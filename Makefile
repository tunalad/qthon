INSTALL_DIR = $(HOME)/.local/bin
BINARY_NAME = qthon

build:
	python3 build.py

install: build
	install -m 755 dist/$(BINARY_NAME) $(INSTALL_DIR)/$(BINARY_NAME)

uninstall:
	rm -f $(INSTALL_DIR)/$(BINARY_NAME)

clean:
	rm -rf build dist venv_build
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

.PHONY: build install uninstall clean
