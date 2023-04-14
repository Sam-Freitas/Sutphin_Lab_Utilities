import os
import glob
import numpy as np
import shutil
from pathlib import Path
from tqdm import tqdm
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath

# Update settings
# if Set to True then the program will check if there is a newer version and update, or if file doesnt exist then will transfer it
# if false then it will overwrite everything 
update_files = True
# 50MB -> 50000000
max_file_size = 50000000

PATH_TO_WW = os.getcwd()
# PATH_TO_SUTPHIN = "/Volumes/Sutphin server/Projects/Worm Paparazzi/Data"

PATH_TO_SUTPHIN = r"Z:\Projects\Worm Paparazzi\Data"

if os.path.isdir(PATH_TO_SUTPHIN) is not True:
    PATH_TO_SUTPHIN = r"Y:\Projects\Worm Paparazzi\Data"
    
assert os.path.isdir(PATH_TO_SUTPHIN)
assert os.path.isdir(PATH_TO_WW)

EXT = "*.csv"
all_csv_files = [file
                 for path, subdir, files in os.walk(PATH_TO_WW)
                 for file in glob.glob(os.path.join(path, EXT))]

all_csv_files2 = [ x for x in all_csv_files if "division" not in x ]
all_csv_files2 = [ x for x in all_csv_files2 if "Groupname.csv" not in x ]

for i in tqdm(range(len(all_csv_files2))):

    this_filepath = all_csv_files2[i]

    # get filename of csv
    file_name = Path(this_filepath).stem
    # get name of experiment 
    this_dir = os.path.dirname(this_filepath)
    this_dir_name = Path(this_dir).stem
    print('')
    print(this_dir_name)
    # make a new path 
    new_dir_path = os.path.join(PATH_TO_SUTPHIN,this_dir_name)

    file_list = os.listdir(this_dir)

    for this_file in os.listdir(this_dir):
        this_file_path = os.path.join(this_dir,this_file)
        this_file_size = os.path.getsize(this_file_path)
        if this_file_size < max_file_size:
            new_file_path = os.path.join(new_dir_path,this_file)
            if os.path.isdir(this_file_path):
                copy_tree(this_file_path, new_file_path, update=update_files)
            else:
                mkpath(new_dir_path)
                copy_file(this_file_path, new_file_path, update=update_files)

