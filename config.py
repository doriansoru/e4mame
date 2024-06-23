import configparser
import gettext
import locale
import pathlib
import xml.etree.ElementTree as ET
from platformdirs import user_config_dir

# Sets the default locale
locale.setlocale(locale.LC_ALL, "")
# Gets the default encoding
encoding = locale.getencoding()

# Gets the default locale
lang, _ = locale.getlocale()

if lang:
	g = gettext.translation("base", localedir="locales")
	_ = g.gettext
else:
	gettext.install(True)

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

	# Remove empty strings from the list
	games_list = [game for game in roms if game]

	# Sort games
	games_list.sort()

	games = {}
	n = len(games_list)
	i = 1
	snaps_list = []
	with zipfile.ZipFile(config["snap_file"], "r") as snaps:
		snaps_list = snaps.namelist()

	for game in games_list:
		print(_("Checking for") + " " + str(i) + " / " + str(n) + ": " + game + "...")
		snap_name = f"{game}.png"
		command = [config['mame_executable'], "-lx", game]
		process = subprocess.Popen(command, stdout=subprocess.PIPE)
		output, error = process.communicate()

		# L'output sarà in bytes, quindi lo convertiamo in una stringa
		xml_string = output.decode()

		root = ET.fromstring(xml_string)
		for machine in root.findall(f'.//machine[@name="{game}"]'):
			description = machine.find(FLD_DESCRIPTION).text

		snapshot = snap_name in snaps_list
		games[game] = {FLD_DESCRIPTION: description, "snapshot": snapshot}
		i += 1
	print(_("Saving everything in") + " " + config["games_file"])
	with open(config["games_file"], "w") as f:
		json.dump(games, f, indent=4)
