config_file = config.ini

all: $(config_file) install_requirements


$(config_file): create_config

create_config:
	@if [ ! -f $(config_file) ]; then \
		echo "[global]" > $(config_file) && \
		echo "Enter your roms path:" && \
		read config_value && \
		echo "rom_path = $$config_value" >> $(config_file) && \
		echo "Enter the full path and name of your snaps zip file:" && \
		read config_value && \
		echo "snap_file = $$config_value" >> $(config_file) && \
		echo "Enter the full path of your mame executable:" && \
		read config_value && \
		echo "mame_executable = $$config_value" >> $(config_file) && \
		echo "$(config_file) has been created."; \
	fi

install_requirements:
	pip install -r requirements.txt