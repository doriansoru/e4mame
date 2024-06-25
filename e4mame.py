from config import get_config, copy_config_files, _
from const import APP_TITLE, MIN_WIDTH, MIN_HEIGHT, LBL_ADD_TO_FAVORITES, LBL_REMOVE_FROM_FAVORITES, LBL_LAUNCH, LBL_SEARCH, LBL_ALL_GAMES, LBL_FAVORITES, LBL_QUIT, FLD_DESCRIPTION, ALL_GAMES_FRONTEND, FAVORITES_GAMES_FRONTEND
import io
import json
import os
import subprocess
import sys
import tkinter as tk
import tkinter.constants as tkconst
from tkinter import messagebox
from tkinter import ttk, font
import zipfile
from PIL import Image, ImageTk
import pyperclip

class E4Mame:
	"""
	Class that handles the graphical interface of the MAME frontend.
	"""

	def __init__(self, window, source, search=True, show_favorites=False, manager = None):
		"""
		Initialize the E4Mame class.

		:param window: The main window of the application.
		:param source: The path to the JSON file that contains the games list.
		:param search: Boolean that indicates if the search bar should be displayed.
		:param show_favorites: Boolean that indicates if the favorites games should be displayed.
		:param manager: A reference to the E4MameManager class for all instances of this class.
		"""

		self.window = window
		self.manager = manager
		self.window.bind("<Configure>", self.on_window_resize)

		self.source = source
		self.search = search
		self.show_favorites = show_favorites
		self.pad = 20

		self.config = get_config(True)
		# Copy the config file
		if not os.path.isdir(self.config["config_dir"]):
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
		self.info_label = tk.Label(
			self.info_frame,
			text=_("Double click to launch the game, right click for more options"),
			font=font.Font(size=18),
		)

		self.info_label.pack(
			side=tk.TOP, fill=tk.X, padx=(self.pad, self.pad), pady=(self.pad, self.pad)
		)

		# Creates a game list
		self.game_list = tk.Listbox(self.game_list_frame, font=font.Font(size=12))
		self.game_list.bind("<KeyPress>", lambda event: self.on_key_press(event.char))
		self.game_list.bind("<<ListboxSelect>>", self.on_game_select)
		self.game_list.bind("<Double-Button-1>", self.launch_game)

		# Popup menu
		self.menu = tk.Menu(self.window, tearoff=0)
		self.menu.add_command(label=LBL_LAUNCH, command=self.launch_game)
		self.menu.add_command(
			label=LBL_REMOVE_FROM_FAVORITES, command=self.remove_favorite
		)
		self.menu.add_separator()
		self.menu.add_command(label=LBL_QUIT, command=self.window.quit)
		self.game_list.bind("<Button-3>", self.popup)

		scrollbar = tk.Scrollbar(
			self.game_list_frame, orient=tk.VERTICAL, command=self.game_list.yview
		)
		self.scrollbar = scrollbar
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
		self.game_list.config(yscrollcommand=scrollbar.set)

		# Modify the listbox to let space for the scrollbar
		self.game_list.pack(
			side=tk.TOP, fill=tk.BOTH, expand=True, padx=(self.pad, self.pad)
		)

		# Creates a frame for the favorite button and search bar
		self.search_fav_frame = tk.Frame(self.game_list_frame)
		self.search_fav_frame.pack(side=tk.TOP, fill=tk.X)

		# Creates a search bar (if search is True)
		if self.search:
			self.search_var = tk.StringVar()
			self.search_var.trace("w", self.search_games)
			self.search_entry = tk.Entry(
				self.search_fav_frame, textvariable=self.search_var
			)
			self.search_entry.pack(
				side=tk.LEFT,
				fill=tk.X,
				expand=True,
				padx=(self.pad, self.pad),
				pady=(self.pad, self.pad),
			)
			self.search_label = tk.Label(
				self.search_fav_frame, text=LBL_SEARCH, font=font.Font(size=13)
			)
			self.search_label.pack(
				side=tk.LEFT, padx=(self.pad, self.pad), pady=(self.pad, self.pad)
			)

		if not os.path.exists(self.source):
			self.games = {}
		else:
			# Loads the JSON file with game information
			with open(self.source, "r") as f:
				self.games = json.load(f)

		# Adds games to the list
		for game in sorted(
			self.games.keys(), key=lambda x: self.games[x][FLD_DESCRIPTION]
		):
			self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])

		# Creates a frame for the game image
		self.game_image_frame = ttk.Frame(self.window)
		self.game_image_frame.pack(
			side=tk.TOP,
			fill=tk.BOTH,
			expand=True,
			padx=(self.pad, self.pad),
			pady=(self.pad, self.pad),
		)

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
			with open(self.config["favorites_file"], "r") as f:
				favorites = json.load(f)
		except FileNotFoundError:
			favorites = {}
		except (PermissionError, IsADirectoryError) as e:
			self.error(e, True)
			favorites = {}
		return favorites

	def save_favorites(self):
		"""
		Save the favorites games to the JSON file.
		"""
		
		# Saves the favorites
		with open(self.config["favorites_file"], "w") as f:
			json.dump(self.favorites, f)

		self.favorites = self.load_favorites()

		# Updates the list in the second tab
		favorites_games_frontend = self.manager.get_instance(FAVORITES_GAMES_FRONTEND)
		
		if favorites_games_frontend is not None:
			favorites_games_frontend.load_games()

	def add_favorite(self, selected_game):
		"""
		Add a game to the favorites.

		:param selected_game: The name of the game to add to the favorites.
		"""
		# Adds the selected game to the favorites
		self.favorites[selected_game] = self.games[selected_game]
		self.save_favorites()

	def error(self, message, terminate = False):
		"""
		Shows an error messagebox.
		
		:param message: The string of the message to show.
		:param terminate: Terminate or not the program after the error.
		"""
		# Show a messagebox
		messagebox.showerror(_("Error"), message)
		if terminate:
			sys.exit()
		
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
			for idx, game_name in enumerate(self.game_list.get(0, tkconst.END)):
				if game_name.lower().startswith(letter.lower()):
					self.game_list.see(idx)
					self.game_list.selection_clear(0, tk.END)
					self.game_list.selection_set(idx)
					self.on_game_select(None)
					break
		elif letter in ("\r", "\n"):
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
				if (
					self.search_var.get().lower()
					in self.games[game][FLD_DESCRIPTION].lower()
				):
					self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])
		else:  # If the search string is empty
			for game in sorted(
				self.games.keys(), key=lambda x: self.games[x][FLD_DESCRIPTION]
			):
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
			game
			for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description
		)

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
			try:
				with zipfile.ZipFile(self.config["snap_file"], "r") as snaps:
					img_data = snaps.read(game_image_name)
			except (FileNotFoundError, PermissionError, zipfile.BadZipFile) as e:
				self.error(e, True)

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

	def launch_game(self, event=None):
		"""
		Launch the selected game.

		:param event: The event object.
		"""
		# Gets the selected game
		selected_game_description = self.game_list.get(tk.ACTIVE)
		selected_game = next(
			game
			for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description
		)

		# Launches the selected game with MAME
		try:
			result = subprocess.run(
				[self.config["mame_executable"], selected_game],
				capture_output=True,
				check=False,
			)
		except (subprocess.CalledProcessError, FileNotFoundError) as e:
			self.error(e)
		
		if result.stderr.decode() != "":
			error_message = (
				_("An error occurred while running the game:")
				+ f"\n\n{result.stderr.decode()}"
				+ "\n\n"
				+ _("The error message has been copied in the clipboard")
			)
			pyperclip.copy(result.stderr.decode())
			self.error(error_message)

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
		for game in sorted(
			self.games.keys(), key=lambda x: self.games[x][FLD_DESCRIPTION]
		):
			self.game_list.insert(tk.END, self.games[game][FLD_DESCRIPTION])

	def popup(self, event):
		"""
		Handle the right-click event in the games list and display a popup menu.

		:param event: The event object.
		"""
		# Modify the second voice of the menu
		selected_game_description = self.game_list.get(tk.ACTIVE)
		selected_game = next(
			game
			for game in self.games
			if self.games[game][FLD_DESCRIPTION] == selected_game_description
		)
		if selected_game in self.favorites:
			self.menu.entryconfig(
				1,
				label=LBL_REMOVE_FROM_FAVORITES,
				command=lambda: self.remove_favorite(selected_game),
			)
		else:
			self.menu.entryconfig(
				1,
				label=LBL_ADD_TO_FAVORITES,
				command=lambda: self.add_favorite(selected_game),
			)

		self.menu.tk_popup(event.x_root, event.y_root)
