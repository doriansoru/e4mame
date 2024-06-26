from const import *
from i18n import _
import configparser
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
import json
import os
import pathlib
import shutil
import subprocess
import xml.etree.ElementTree as ET
from platformdirs import user_config_dir
import zipfile

def get_config(read_from_config_dir=False):
	"""
	Get the configuration variables.
	
	:param read_from_config_dir: If True, read the config.ini file
		   from user_config_dir(app_name), otherwise from the script directory.
	"""

	app_name = "e4mame"
	config_file = "config.ini"
	games_file = "games.json"
	favorites_file = "favorites.json"
	config_dir = user_config_dir(app_name)
	config_dir_path = pathlib.Path(config_dir)

	config = configparser.ConfigParser()
	config.read(config_file)
	rom_path = config["global"]["rom_path"]
	snap_file = config["global"]["snap_file"]
	mame_executable = config["global"]["mame_executable"]

	config = {"config_file": config_file, 
		"games_file": (config_dir_path / games_file) if read_from_config_dir else games_file,
		"favorites_file": (config_dir_path / favorites_file) if read_from_config_dir else favorites_file,
		"config_dir": config_dir,
		"rom_path": rom_path,
		"snap_file": snap_file,
		"mame_executable": mame_executable,
	}
	return config

def copy_config_files():
	"""
	Copy the configuration files to config["config_dir"].
	"""

	config = get_config(False)
	# Copy the config file
	if not os.path.isdir(config["config_dir"]):
		# Create the directory
		os.makedirs(config["config_dir"], exist_ok=True)
		shutil.copy(config["config_file"], config["config_dir"])
		shutil.copy(config["games_file"], config["config_dir"])

def check_game(game, config, snaps_list):
	"""
	Checks if a game is functional by running the MAME executable and parsing the output.

	:param game: The name of the game to check
	:param config: The configuration variables
	:param snaps_list: List of available snapshots
	"""
	snap_name = f"{game}.png"
	command = [config['mame_executable'], "-lx", game]
	process = subprocess.Popen(command, stdout=subprocess.PIPE)
	output, error = process.communicate()

	# The output will be in bytes, convert it to a string
	xml_string = output.decode()

	root = ET.fromstring(xml_string)
	description = None
	for machine in root.findall(f'.//machine[@name="{game}"]'):
		description = machine.find(FLD_DESCRIPTION).text

	snapshot = snap_name in snaps_list
	return game, {FLD_DESCRIPTION: description, "snapshot": snapshot}

def check_games(games_list, config, snaps_list):
	"""
	Checks multiple games for functionality using multiple cores.

	:param games_list: List of game names to check
	:param config: The configuration variables
	:param snaps_list: List of available snapshots
	"""	
	games = {}
	i = 1
	n = len(games_list)

	with ProcessPoolExecutor() as executor:
		futures = {executor.submit(check_game, game, config, snaps_list): game for game in games_list}

		for future in as_completed(futures):
			game, result = future.result()
			games[game] = result
			print(_("Checking for") + " " + str(i) + " / " + str(n) + ": " + game + "...")
			i += 1

	return games	
	
def build_games(config, custom_xml=None):
	"""
	Build the working game list.

	:param config: The configuration variables
	:param custom_xml: A custom xml file instead of that one returned by mame -listxml.
	"""

	config = get_config(False)

	print(_("Getting all your roms list..."))
	if custom_xml is None:
		command = [config['mame_executable'], "-listxml"]
		process = subprocess.run(
			command, stdout=subprocess.PIPE, check=False
		)
		xml_string = process.stdout.decode()
	else:
		with open(custom_xml, "r") as f:
			xml_string = f.read()

	try:
		root = ET.fromstring(xml_string)
	except ET.ParseError as e:
		print(_("Error") + "\n\n" + str(e))

	machines = root.findall("machine")
	roms = [
		machine.attrib["name"]
		for machine in machines
		if machine.attrib["isbios"] == "no"
		and machine.find(".//driver") is not None
		and machine.find(".//driver").attrib["status"] == "good"
	]

	# Remove empty strings and non existent zip files for romsfrom the list
	games_list = [ game for game in roms if game and (pathlib.Path(config['rom_path']) / f"{game}.zip").is_file() ]

	# Sort games
	games_list.sort()

	games = {}
	n = len(games_list)
	i = 1
	snaps_list = []
	with zipfile.ZipFile(config["snap_file"], "r") as snaps:
		snaps_list = snaps.namelist()

	games = check_games(games_list, config, snaps_list)
		
	print(_("Saving everything in") + " " + config["games_file"])
	with open(config["games_file"], "w") as f:
		json.dump(games, f, indent=4)
