import PyInstaller.__main__
import os
import sys

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Determine the path separator based on the OS
sep = ';' if sys.platform == 'win32' else ':'

PyInstaller.__main__.run([
    'desk_pet.py',
    '--onefile',
    '--windowed',
    '--name=CrystalLizardPet',
    f'--add-data=pet.png{sep}.',
    f'--add-data=petopen.png{sep}.',
    f'--add-data=petsleep.png{sep}.',
    f'--add-data=speechbubble.png{sep}.',
    '--clean',
]) 