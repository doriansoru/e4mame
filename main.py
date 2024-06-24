from config import get_config, copy_config_files, build_games, _
from e4mame import E4Mame
import argparse
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk, font
import zipfile

APP_TITLE = _("E4 MAME Frontend")
MIN_WIDTH = 600
MIN_HEIGHT = 400

LBL_ADD_TO_FAVORITES = _("Add to favorites")
LBL_REMOVE_FROM_FAVORITES = _("Remove from favorites")
LBL_LAUNCH = _("Launch")
LBL_SEARCH = _("Type to search")
LBL_ALL_GAMES = _("All games")
LBL_FAVORITES = _("Favorites")
LBL_QUIT = _("Quit")

FLD_DESCRIPTION = "description"

def get_about_notebook():
	"""
	Build and return the about notebook tab.
	"""

	# Adds an "About" notebook
	pad1 = 30
	pad2 = 20
	about_notebook = ttk.Frame(notebook)
	label_app_name = ttk.Label(about_notebook, text=APP_TITLE, font=font.Font(size=25))
	label_app_description = ttk.Label(
		about_notebook, text=_("A minimalistic MAME Frontend"), font=font.Font(size=16)
	)
	label_app_author = ttk.Label(
		about_notebook,
		text="by Dorian Soru, doriansoru@gmail.com",
		font=font.Font(size=14),
	)
	label_license = ttk.Label(
		about_notebook,
		text=_("Released under the GPL-3.0 Licence"),
		font=font.Font(size=14),
	)

	# Add the elements
	label_app_name.pack(fill=tk.X, pady=(0, pad1))
	label_app_description.pack(fill=tk.X, pady=(0, pad2))
	label_app_author.pack(fill=tk.X, pady=(0, pad2))
	label_license.pack(fill=tk.X, pady=(0, pad2))
	return about_notebook


if __name__ == "__main__":
	# Parse arguments
	parser = argparse.ArgumentParser(description=APP_TITLE)
	parser.add_argument("-g", "--games", action="store_true", help="Build games list")
	parser.add_argument(
		"-x", "--xml", type=str, help="Path to your MAME custom XML file"
	)
	args = parser.parse_args()

	# Get the config file from the current directory
	config = get_config(False)

	# Check if games_file exists or creates it
	if not os.path.isfile(config["games_file"]):
		print(_("The games file does not exist. I will now create it."))
		print(
			_("Please confirm that your zip snap file is:") + " " + config["snap_file"]
		)
		print(
			_("Please confirm that your mame executable is:")
			+ " "
			+ config["mame_executable"]
		)
		confirm = input(_("Y") + " / " + _("N") + ": ").lower()
		if confirm == _("N").lower():
			print(_("Please correct") + " " + config["config_file"])
			sys.exit()
		else:
			if args.xml is not None:
				build_games(config, args.xml)
			else:
				build_games(config)
			copy_config_files()
			print(_("All files have been update. Please restart the program"))
			sys.exit()

	# Now user_config_dir(app_name) has been created and
	# the config files have been copied. Re-read them from there
	config = get_config(True)

	# Appropriate actions for the various arguments
	if args.games:
		if args.xml is not None:
			build_games(config, args.xml)
		else:
			build_games(config)
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
		all_games_frontend = E4Mame(
			all_games_frame, config["games_file"], search=True, show_favorites=False
		)

		# Adds the first tab to the notebook
		notebook.add(all_games_frame, text=LBL_ALL_GAMES)

		# Creates a frame for the second tab
		favorites_games_frame = ttk.Frame(notebook)

		# Creates an instance of MameFrontend for the second tab
		favorites_games_frontend = E4Mame(
			favorites_games_frame,
			config["favorites_file"],
			search=True,
			show_favorites=True,
		)

		# Adds the second tab to the notebook
		notebook.add(favorites_games_frame, text=LBL_FAVORITES)

		# Add the tab
		notebook.add(get_about_notebook(), text=_("About"))

		window.after_idle(lambda: all_games_frontend.select_first_game())
		# Starts the main window
		window.mainloop()
