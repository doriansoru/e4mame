import gettext
import locale

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
