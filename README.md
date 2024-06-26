# E4 Mame Frontend

This is a simple MAME Frontend written in Python.

## Description
I needed a minimalistic MAME Frontend and, after searching for a while, I decided to write this one in Python.

![Screenshot of the program](https://github.com/doriansoru/e4mame/assets/96388235/6ec1813f-fd75-47d0-80a6-325104e6d10f)

## Getting Started

### Dependencies
Dependencies can be installed by running
```pip install -r requirements.txt```
from the program directory.

* Pillow for resizing the snapshot images.
* Plaformdirs to get the current user config directory.
* Pyperclip to automatically copy error messages on the clipboard.

### Installing

* On Unix systems type `make` to build a personalized config.ini file and to run `pip install -r requirements.txt`.
* Otherwise, modify `config.ini.sample` and rename it to `config.ini` and run yourself `pip install -r requirements.txt`.

### Executing program

* Open a shell
* Go to the script directory
* Type:
```python3 main.py```

The first time it runs, it will create games.json, the list of all working games, by analysing the result of `mame -listxml`. You can also provide your custom xml roms list by using `--xml` argument.
You can rebuild the games list by using the `--games` argument, than you need to copy games.json in your config directory (in unix systems it is usually `~/.config/e4mame`)-

## Help

For getting help type:
```
python3 main.py -h
```

## Authors

For any question please feel free to [contact me](mailto:doriansoru@gmail.com).

## Version History
* 0.1
    * Initial Release

## License

This project is licensed under the GNU General Public License Version 3 - see the LICENSE file for details.
