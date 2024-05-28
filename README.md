# E4 Mame Frontend

This is a simple MAME Frontend written in python.

## Description

I needed a minimalistic MAME Frontend and, after searching for a while, I decided to write this one in Python.

## Getting Started

### Dependencies
Dependencies can be installed by running
```pip -r requirements.txt```
from the program directory.

* Pillow for resizing the snapshot images.
* Plaformdirs to get the current user config directory.

### Installing

* On Unix systems type `make` to build a personalized config.ini file and to run `pip -r requirements.txt`.
* Otherwise, modify `config.ini.sample` and rename it to `config.ini` and run yourself `pip -r requirements.txt`.

### Executing program

* Open a shell
* Go to the script directory
* Type:
```python3 e4mame.py```

The first time it runs, it will create games.json, the list of all working games, by analysing the result of `mame -listxml`. You can also provide your custom xml roms list by using `--xml` argument.
You can rebuild the games list by using the `--games` argument, than you need to copy games.json in your config directory (in unix systems it is usually `~/.config/e4mame`)-

## Help

For getting help type:
```
python3 e4mame.py -h
```

## Authors

For any question please feel free to [contact me](mailto:doriansoru@gmail.com).

## Version History
* 0.1
    * Initial Release

## License

This project is licensed under the GNU General Public License Version 3 - see the LICENSE.md file for details.
