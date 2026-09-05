INSTALL_DIR = $(HOME)/.local/bin
BINARY_NAME = qthon

WINEPREFIX = $(HOME)/.wine-pyinstaller
WINE_PYTHON_VER = 3.11.9
WINE_PYTHON_URL = https://www.python.org/ftp/python/$(WINE_PYTHON_VER)/python-$(WINE_PYTHON_VER)-amd64.exe
WINE_GIT_URL = https://github.com/git-for-windows/git/releases/download/v2.55.0.windows.4/MinGit-2.55.0.4-64-bit.zip
VGIO_TARBALL = https://github.com/joshuaskelly/vgio/archive/refs/heads/features/half-life.tar.gz

build:
	python3 build.py

wine-init:
	WINEARCH=win64 WINEPREFIX=$(WINEPREFIX) wineboot
	curl -LO $(WINE_PYTHON_URL)
	WINEPREFIX=$(WINEPREFIX) wine python-$(WINE_PYTHON_VER)-amd64.exe /quiet InstallAllUsers=0 PrependPath=1
	WINEPREFIX=$(WINEPREFIX) wineserver -w
	rm -f python-$(WINE_PYTHON_VER)-amd64.exe
	curl -L $(WINE_GIT_URL) -o mingit.zip
	unzip -q -o mingit.zip -d $(WINEPREFIX)/drive_c/MinGit
	rm -f mingit.zip

wine-build:
	WINEPREFIX=$(WINEPREFIX) WINEPATH="$(WINEPREFIX)/drive_c/MinGit/cmd" wine python build.py

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

.PHONY: build wine-init wine-build install uninstall clean
