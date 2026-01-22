import os, glob, natsort, time, shutil
import numpy as np
import pandas as pd
# import shutil
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath
from sys import platform

print('Operating system:')
print(platform)

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
assert os.path.isfile(PATH_TO_DIVISION_BASE)

print("Path to Sutphin", PATH_TO_SUTPHIN)
print("Path to division template", PATH_TO_DIVISION_BASE)

base_division = pd.read_csv(PATH_TO_DIVISION_BASE)
base_columns = base_division.columns

# print(base_division)

print('All paths have been verified')
print('Recursively looking up all .CSV files in', str(PATH_TO_SUTPHIN))

#recursively get all the csv files from the _Data folder
# the csvs are used to locate the folder that contains all the processed data
EXT = "*.csv"
# t_old = time.time()
# all_csv_files = [file
#                  for path, subdir, files in os.walk(PATH_TO_WW)
#                  for file in glob.glob(os.path.join(path, EXT))]
# t_old = time.time() - t_old

t_new = time.time()
all_csv_files = []
for i, this_path in enumerate(tqdm(Path(PATH_TO_SUTPHIN).rglob(EXT))):
    all_csv_files.append(str(this_path))
t_new = time.time() - t_new

# get all the division paths for the data lookup table
division_csv_files = [ x for x in all_csv_files if "division" in x ]
division_csv_files = natsort.natsorted(division_csv_files)

# get the base divisions
base_division = pd.read_csv(PATH_TO_DIVISION_BASE)
base_columns = base_division.columns

# get rid of unnecessary csvs
cleaned_csv_files = [ x for x in all_csv_files if "division" not in x ]
cleaned_csv_files = [ x for x in cleaned_csv_files if "Groupname.csv" not in x ]

cleaned_csv_files = natsort.natsorted(cleaned_csv_files)

for i in tqdm(range(len(cleaned_csv_files))):

    this_filepath = cleaned_csv_files[i]

    split_path = os.path.split(this_filepath)
    path_without_csv = os.path.join(split_path[0])

    print(split_path)
    

    img_path = os.path.join(path_without_csv,'processed_img_data')

    if os.path.isdir(img_path):
        print(path_without_csv)
        shutil.rmtree(img_path)

    # if file_name
