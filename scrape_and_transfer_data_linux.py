import os, glob, natsort
import numpy as np
import pandas as pd
# import shutil
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath

# this script scrapes all the data from the _Data folder from worm paparazzi 
# then transfers it into the regular holding in the Sutphin server

# this additionally makes a lookup table for easy checking of experiments that have already
# been created and easy to lookup
# the lookup table has the N/NC, mean/median life/healthspan 

# Update settings
# if Set to True then the program will check if there is a newer version and update, or if file doesnt exist then will transfer it
# if false then it will overwrite everything 
update_files = True
# 50MB -> 50000000
max_file_size = 50000000

# get all the paths and directories of the 
# PATH_TO_WW = os.getcwd()
PATH_TO_WW = r"Z:\_Data"
if os.path.isdir(PATH_TO_WW) is not True:
    PATH_TO_WW = "/volume1/WormWatcher/_Data"

# PATH_TO_SUTPHIN = "/Volumes/Sutphin server/Projects/Worm Paparazzi/Data"
PATH_TO_SUTPHIN = r"Z:\Projects\Worm Paparazzi\Data"
if os.path.isdir(PATH_TO_SUTPHIN) is not True:
    PATH_TO_SUTPHIN = r"Y:\Projects\Worm Paparazzi\Data"
    if os.path.isdir(PATH_TO_SUTPHIN) is not True:
        PATH_TO_SUTPHIN = "/volume2/Sutphin server/Projects/Worm Paparazzi/Data"

PATH_TO_DIVISION_BASE = r"Z:\Worm_Paparazzi\Data_setup\Groupname_divisions.csv"
if os.path.isfile(PATH_TO_DIVISION_BASE) is not True:
    PATH_TO_DIVISION_BASE = "/volume1/WormWatcher/Worm_Paparazzi/Data_setup/Groupname_divisions.csv"

assert os.path.isdir(PATH_TO_SUTPHIN)
assert os.path.isdir(PATH_TO_WW)
assert os.path.isfile(PATH_TO_DIVISION_BASE)

print("Path to Sutphin", PATH_TO_SUTPHIN)
print("Path to WW", PATH_TO_WW)
print("Path to division template", PATH_TO_DIVISION_BASE)

print('All paths have been verified')
print('Recursively looking up all .CSV files in', str(PATH_TO_WW))