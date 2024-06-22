import argparse
import configparser
import json
import os
from PIL import Image, ImageTk
from platformdirs import *
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, font
import xml.etree.ElementTree as ET
import gettext
import locale
import zipfile
import io
import pyperclip

# Sets the default locale
locale.setlocale(locale.LC_ALL, '')
# Gets the default encoding
encoding = locale.getencoding()

# Gets the default locale
lang, _ = locale.getlocale()

if lang:
	g = gettext.translation('base', localedir='locales')
	_ = g.gettext
else:
	gettext.install(True)

APP_TITLE = _('E4 MAME Frontend')
MIN_WIDTH = 600
MIN_HEIGHT = 400

LBL_ADD_TO_FAVORITES = _('Add to favorites')
LBL_REMOVE_FROM_FAVORITES = _('Remove from favorites')
LBL_LAUNCH = _('Launch')
LBL_SEARCH = _('Type to search')
LBL_ALL_GAMES = _('All games')
LBL_FAVORITES = _('Favorites')
LBL_QUIT = _('Quit')

FLD_DESCRIPTION = 'description'

class E4Mame:
	"""
	Class that handles the graphical interface of the MAME frontend.
	"""
	def __init__(self, window, source, search=True, show_favorites=False):
		"""
		Initialize the E4Mame class.

		:param window: The main window of the application.
		:param source: The path to the JSON file that contains the games list.
		:param search: Boolean that indicates if the search bar should be displayed.
		:param show_favorites: Boolean that indicates if the favorites games should be displayed.
		"""
				
		self.window = window
		self.window.bind("<Configure>", self.on_window_resize)

		self.source = source
		self.search = search
		self.show_favorites = show_favorites
		self.PAD = 20

		self.config = get_config(True)
		# Copy the config file
		if not os.path.isdir(config['config_dir']):
			copy_config_files()
			self.config = get_config(True)

		self.favorites = self.load_favorites()

		# Creates a frame for the game list
		self.game_list_frame = tk.Frame(self.window)
		self.game_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		# Creates a frame for the info label
		self.info_frame = ttk.Frame(self.game_list_frame)
		self.info_frame.pack(side=tk.TOP, fill=tk.X)

		# Creates a label at the beginning
		self.info_label = tk.Label(self.info_frame, text=_("Double click to launch the game, right click for more options"), font=font.Font(size = 18))
		self.info_label.pack(side=tk.TOP, fill=tk.X, padx=(self.PAD, self.PAD), pady=(self.PAD, self.PAD))

		# Creates a game list
		self.game_list = tk.Listbox(self.game_list_frame, font=font.Font(size=12))
		self.game_list.bind("<KeyPress>", lambda event: self.on_key_press(event.char))
		self.game_list.bind('<<ListboxSelect>>', self.on_game_select)
		self.game_list.bind("<Double-Button-1>", self.launch_game)

		# Popup menu
		self.menu = tk.Menu(self.window, tearoff=0)
		self.menu.add_command(label = LBL_LAUNCH, command=self.launch_game)
		self.menu.add_command(label = LBL_REMOVE_FROM_FAVORITES,
									  command=self.remove_favorite)
		self.menu.add_separator()
		self.menu.add_command(label = LBL_QUIT, command=self.window.quit)
		self.game_list.bind("<Button-3>", self.popup)

		scrollbar = tk.Scrollbar(self.game_list_frame, orient=tk.VERTICAL, command = self.game_list.yview)
		self.scrollbar = scrollbar
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.game_list.config(yscrollcommand=scrollbar.set)

		# Modify the listbox to let space for the scrollbar
		self.game_list.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(self.PAD, self.PAD))

		# Creates a frame for the favorite button and search bar
		self.search_fav_frame = tk.Frame(self.game_list_frame)
		self.search_fav_frame.pack(side=tk.TOP, fill=tk.X)

		# Creates a search bar (if search is True)
		if self.search:
			self.search_var = tk.StringVar()
			self.search_var.trace('w', self.search_games)
			self.search_entry = tk.Entry(self.search_fav_frame,
										   textvariable=self.search_var)
			self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(self.PAD, self.PAD), pady=(self.PAD, self.PAD))
			self.search_label = tk.Label(self.search_fav_frame, text = LBL_SEARCH, font=font.Font(size = 13))
			self.search_label.pack(side=tk.LEFT, padx=(self.PAD, self.PAD), pady=(self.PAD, self.PAD))

		if not os.path.exists(self.source):
			self.games = {}
		else:
			# Loads the JSON file with game information
			with open(self.source, "r") as f:
				self.games = json.load(f)

		# Adds games to the list
		for game in sorted(self.games.keys(),
						   key=lambda x: self.games[x][FLD_DESCRIPTION]):
			self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])

		# Creates a frame for the game image
		self.game_image_frame = ttk.Frame(self.window)
		self.game_image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=(self.PAD, self.PAD), pady=(self.PAD,self.PAD))

		# Creates a label for the game image
		self.game_image_label = tk.Label(self.game_image_frame)
		self.game_image_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		self.game_image = None
		self.game_image_tk = None

		# Updates the game description and image at startup
		self.on_game_select(None)

	def load_favorites(self):
		"""
		Load the favorites games from the JSON file.
		"""		
		try:
			with open(self.config['favorites_file'], "r") as f:
				favorites = json.load(f)
		except FileNotFoundError:
			favorites = {}
		return favorites

	def save_favorites(self):
		"""
		Save the favorites games to the JSON file.
		"""		
		# Saves the favorites
		with open(self.config['favorites_file'], "w") as f:
			json.dump(self.favorites, f)

		self.favorites = self.load_favorites()

		# Updates the list in the second tab
		if favorites_games_frontend:
			favorites_games_frontend.load_games()

	def add_favorite(self, selected_game):
		"""
		Add a game to the favorites.

		:param selected_game: The name of the game to add to the favorites.
		"""		
		# Adds the selected game to the favorites
		self.favorites[selected_game] = self.games[selected_game]
		self.save_favorites()

	def remove_favorite(self, selected_game):
		"""
		Remove a game from the favorites.

		:param selected_game: The name of the game to remove from the favorites.
		"""		
		# Removes the selected game from the favorites
		if selected_game in self.favorites:
			del self.favorites[selected_game]

		# Saves the favorites
		self.save_favorites()

	def on_key_press(self, letter):
		"""
		Handle the key press event in the games list.

		:param letter: The letter that was pressed.
		"""		
		if letter.isalpha():
			for idx in range(self.game_list.size()):
				game_name = self.game_list.get(idx)
				if game_name.lower().startswith(letter.lower()):
					self.game_list.see(idx)
					self.game_list.selection_clear(0, tk.END)
					self.game_list.selection_set(idx)
					self.on_game_select(None)
					break
		elif letter == '\r' or letter == '\n':
			self.launch_game()

	def search_games(self, *args):
		"""
		Search the games list and display the results.
		"""		
		# Clears the game list
		self.game_list.delete(0, tk.END)

		# Adds games that contain the search string to the list
		if self.search_var.get():  # If the search string is not empty
			for game in self.games.keys():
				if (self.search_var.get().lower()
						in self.games[game][FLD_DESCRIPTION].lower()):
					self.game_list.insert(tk.END,
										  self.games[game][FLD_DESCRIPTION])
		else:  # If the search string is empty
			for game in sorted(self.games.keys(),
							   key=lambda x: self.games[x][FLD_DESCRIPTION]):
				self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])

	def select_first_game(self):
		"""
		Select the first game in the games list.
		"""		
		# Selects the first game
		self.game_list.selection_clear(0, tk.END)
		self.game_list.activate(0)
		self.game_list.selection_set(0)
		self.on_game_select(None)

	def on_tab_select(self, event):
		"""
		Handle the tab select event.

		:param event: The event object.
		"""		
		# Selects the first game if no game is selected
		if len(self.game_list.curselection()) == 0:
			self.select_first_game()
			
	def on_window_resize(self, event=None):
		"""
		Handle the window resize event.

		:param event: The event object.
		"""
		if self.game_image is None:
			return

		# Resize the game image
		margin = self.scrollbar.winfo_width() + self.info_frame.winfo_height()
		window_height = self.window.winfo_height()
		new_height = window_height - margin
		ratio = new_height / self.game_image.height
		new_width = int(self.game_image.width * ratio)
		if new_width <= 0 or new_height <= 0:
			return
		self.game_image = self.game_image.resize((new_width, new_height), Image.LANCZOS)

		# Converts the PIL image to a Tkinter image and displays it in the Label widget
		self.game_image_tk = ImageTk.PhotoImage(self.game_image)
		self.game_image_label.config(image=self.game_image_tk)
		self.game_image_label.image = self.game_image_tk

	def on_game_select(self, event):
		"""
		Handle the game select event.

		:param event: The event object.
		"""		
		if len(self.games) == 0:
			return
		# Checks if a game is selected
		if len(self.game_list.curselection()) == 0:
			return

		# Gets the description of the selected game
		selected_game_description = self.game_list.selection_get()

		# Finds the name of the selected game
		selected_game = next(
			game for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description)

		# Updates the image of the selected game
		self.load_game_image(selected_game)

	def load_game_image(self, selected_game):
		"""
		Load the game image and display it.

		:param selected_game: The name of the game.
		"""		
		# Updates the image of the selected game
		if self.games[selected_game]["snapshot"]:
			# Loads the image of the selected game
			game_image_name = f"{selected_game}.png"
			with zipfile.ZipFile(self.config['snap_file'], 'r') as snaps:
				img_data = snaps.read(game_image_name)

			self.game_image = Image.open(io.BytesIO(img_data))

			# Converts the PIL image to a Tkinter image and displays it in the Label widget
			self.game_image_tk = ImageTk.PhotoImage(self.game_image)
			self.game_image_label.config(image=self.game_image_tk)
			self.game_image_label.image = self.game_image_tk
		else:
			# Updates the image label of the selected game with an error message
			self.game_image_label.config(text=_("Snapshot not available"))
			self.game_image_label.config(image=None)
			self.game_image_label.image = None
			self.game_image = None
			self.game_image_tk = None

	def launch_game(self, event = None):
		"""
		Launch the selected game.

		:param event: The event object.
		"""		
		# Gets the selected game
		selected_game_description = self.game_list.get(tk.ACTIVE)
		selected_game = next(
			game for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description)

		# Launches the selected game with MAME
		result = subprocess.run([self.config['mame_executable'], selected_game], capture_output = True)
		if result.stderr.decode() != "":
			error_message = _("An error occurred while running the game:") + f"\n\n{result.stderr.decode()}" + "\n\n" + _("The error message has been copied in the clipboard")
			pyperclip.copy(result.stderr.decode())
			messagebox.showerror(_("Error"), error_message)

	def load_games(self):
		"""
		Load the games list from the JSON file.
		"""		
		# Clears the game list
		self.game_list.delete(0, tk.END)

		# Loads the JSON file with game information
		with open(self.source, "r") as f:
			self.games = json.load(f)

		# Adds games to the list
		for game in sorted(self.games.keys(),
						   key=lambda x: self.games[x][FLD_DESCRIPTION]):
			self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])

	def popup(self, event):
		"""
		Handle the right-click event in the games list and display a popup menu.

		:param event: The event object.
		"""		
		# Modify the second voice of the menu
		selected_game_description = self.game_list.get(tk.ACTIVE)
		selected_game = next(
			game for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description)
		if selected_game in self.favorites:
			self.menu.entryconfig(1, label=LBL_REMOVE_FROM_FAVORITES,
								 command=lambda: self.remove_favorite(selected_game))
		else:
			self.menu.entryconfig(1, label=LBL_ADD_TO_FAVORITES,
								 command=lambda: self.add_favorite(selected_game))

		self.menu.tk_popup(event.x_root, event.y_root)

def build_games(custom_xml = None):
	"""
	Build the working game list.

	:param custom_xml: A custom xml file instead of that one returned by mame -listxml.
	"""		

	config = get_config(False)
	
	print(_('Getting all your roms list...'))
	if custom_xml is None:
		command = f"{config['mame_executable']} -listxml"
		process = subprocess.run(command, stdout=subprocess.PIPE, shell=True, text=True)
		xml_string = process.stdout
	else:
		with open(custom_xml, 'r') as f:
			xml_string = f.read()

	root = ET.fromstring(xml_string)
	machines = root.findall('machine')
	roms = [ machine.attrib['name'] for machine in machines if machine.attrib['isbios'] == 'no' and machine.find('.//driver') is not None and machine.find('.//driver').attrib['status'] == 'good' ]

	# Remove empty strings from the list
	games_list = [game for game in roms if game]

	# Sort games
	games_list.sort()	

	games = {}
	n = len(games_list)
	i = 1
	snaps_list = []
	with zipfile.ZipFile(config['snap_file'], 'r') as snaps:
		snaps_list = snaps.namelist()

	for game in games_list:
		print(_("Checking for") + " " + str(i) + " / " + str(n) + ": " + game + "...")
		snap_name = f"{game}.png"
		command = f"{config['mame_executable']} -lx {game}"
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		output, error = process.communicate()

		# L'output sarà in bytes, quindi lo convertiamo in una stringa
		xml_string = output.decode()

		root = ET.fromstring(xml_string)
		for machine in root.findall(f'.//machine[@name="{game}"]'):
			description = machine.find(FLD_DESCRIPTION).text

		if snap_name in snaps_list:
			snapshot = True
		else:
			snapshot = False
		games[game] = {FLD_DESCRIPTION: description, 'snapshot': snapshot}
		i += 1
	print(_("Saving everything in") + " " + config['games_file'])
	with open(config['games_file'], 'w') as f:
		json.dump(games, f, indent=4)

def get_config(read_from_config_dir = False):
	"""
	Get the configuration variables.

	:param read_from_config_dir: If True, read the config.ini file from user_config_dir(APP_NAME), otherwise from the script directory.
	"""		

	APP_NAME = 'e4mame'
	CONFIG_FILE = 'config.ini'
	GAMES_FILE = 'games.json'
	FAVORITES_FILE = 'favorites.json'
	config_dir = user_config_dir(APP_NAME)

	config = configparser.ConfigParser()
	config.read(CONFIG_FILE)
	rom_path = config['global']['rom_path']
	snap_file = config['global']['snap_file']
	mame_executable = config["global"]["mame_executable"]

	config = { 
		'config_file': CONFIG_FILE,
		'games_file': os.path.join(config_dir, GAMES_FILE) if read_from_config_dir else GAMES_FILE,
		'favorites_file': os.path.join(config_dir, FAVORITES_FILE) if read_from_config_dir else FAVORITES_FILE,
		'config_dir': config_dir,
		'rom_path': rom_path,
		'snap_file': snap_file,
		'mame_executable': mame_executable
	}
	return config

def copy_config_files():
	"""
	Copy the configuration files to user_config_dir(APP_NAME).
	"""		

	config = get_config(False)
	# Copy the config file
	if not os.path.isdir(config['config_dir']):
		# Create the directory
		os.makedirs(config['config_dir'], exist_ok=True)
		shutil.copy(config['config_file'], self.config_dir)
		shutil.copy(config['games_file'], self.config_dir)


def get_about_notebook():
	"""
	Build and return the about notebook tab.
	"""	

	# Adds an "About" notebook
	pad1 = 30
	pad2 = 20
	about_notebook = ttk.Frame(notebook)
	label_app_name = ttk.Label(about_notebook, text = APP_TITLE, font = font.Font(size = 25))
	label_app_description = ttk.Label(about_notebook, text = _('A minimalistic MAME Frontend'), font = font.Font(size = 16))
	label_app_author = ttk.Label(about_notebook, text = 'by Dorian Soru, doriansoru@gmail.com', font = font.Font(size = 14))
	label_license = ttk.Label(about_notebook, text =_('Released under the GPL-3.0 Licence'), font = font.Font(size = 14))

	# Add the elements
	label_app_name.pack(fill=tk.X, pady = (0, pad1))
	label_app_description.pack(fill=tk.X, pady = (0, pad2))
	label_app_author.pack(fill = tk.X, pady = (0, pad2))
	label_license.pack(fill=tk.X, pady = (0, pad2))
	return about_notebook

if __name__ == "__main__":
	# Parse arguments
	parser = argparse.ArgumentParser(description = APP_TITLE)
	parser.add_argument('-g', '--games', action='store_true', help='Build games list')
	parser.add_argument('-x', '--xml', type=str, help='Path to your MAME custom XML file')
	args = parser.parse_args()

	# Get the config file from the current directory
	config = get_config(False)

	# Check if GAMES_FILE exists or creates it
	if not os.path.isfile(config['games_file']):
		print(_("The games file does not exist. I will now create it."))
		print(_("Please confirm that your zip snap file is:") + " " + config['snap_file'])
		print(_("Please confirm that your mame executable is:") + " " + config['mame_executable'])
		confirm = input(_('Y') + ' / ' + _('N') + ': ').lower()
		if confirm == _('N').lower():
			print(_('Please correct') + ' ' + config['config_file'])
			exit()
		else:
			if args.xml is not None:
				build_games(args.xml)
			else:
				build_games()
			copy_config_files()
			print(_('All files have been update. Please restart the program'))
			exit()
	
	# Now user_config_dir(APP_NAME) has been created and the config files have been copied. Re-read them from there
	config = get_config(True)

	# Appropriate actions for the various arguments
	if args.games:
		if args.xml is not None:
			build_games(args.xml)
		else:
			build_games()
	else:
		# Creates the main window
		window = tk.Tk()
		window.title(APP_TITLE)

		# Sets the minimum dimensions
		window.minsize(MIN_WIDTH, MIN_HEIGHT)

		# Creates an instance of ttk.Notebook
		notebook = ttk.Notebook(window)
		notebook.pack(fill=tk.BOTH, expand=1)

		# Creates a frame for the first tab
		all_games_frame = ttk.Frame(notebook)

		# Creates an instance of MameFrontend for the first tab
		all_games_frontend = E4Mame(all_games_frame,
									 config['games_file'],
									 search=True,
									 show_favorites=False)

		# Adds the first tab to the notebook
		notebook.add(all_games_frame, text = LBL_ALL_GAMES)

		# Creates a frame for the second tab
		favorites_games_frame = ttk.Frame(notebook)

		# Creates an instance of MameFrontend for the second tab
		favorites_games_frontend = E4Mame(favorites_games_frame,
										 config['favorites_file'],
										 search=True,
										 show_favorites=True)

		# Adds the second tab to the notebook
		notebook.add(favorites_games_frame, text = LBL_FAVORITES)

		# Add the tab
		notebook.add(get_about_notebook(), text=_('About'))

		window.after_idle(lambda: all_games_frontend.select_first_game())
		# Starts the main window
		window.mainloop()
