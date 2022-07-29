# Radiolarite
Radiolarite visualizes information from Touchstone files using [Scikit-RF](https://scikit-rf.readthedocs.io/en/latest/), [PyQt5](https://riverbankcomputing.com/software/pyqt/intro), [Matplotlib](https://matplotlib.org/). Radiolarite directly exports to Tikz/PGFPlots using [Tikzplotlib](https://github.com/texworld/tikzplotlib).

I made this tool for the quick analysis of VNA measurements, as I do quite a lot of them for my PhD thesis.

## Installation
Requires installed Python >v3.9

```
python -m venv venv/
venv/Scripts/activate
pip install -r requirements.txt
```
## Usage
Depending on your OS and configuration, the python command may vary.

```
python main.py [optional touchstone filename]
```

This program is still in the very early stages of its development. I add features whenever needed.
