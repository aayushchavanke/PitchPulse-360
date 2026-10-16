"""Executable football data engineering experiments."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'results'/'.matplotlib'))
