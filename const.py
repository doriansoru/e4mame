import gettext
import locale

# Gets the default locale
lang, _ = locale.getlocale()

if lang:
	g = gettext.translation("base", localedir="locales")
	_ = g.gettext
else:
	gettext.install(True)
	
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
