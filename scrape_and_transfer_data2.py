import os
import glob
import numpy as np
import pandas as pd
import shutil
from pathlib import Path
from tqdm import tqdm
from distutils.file_util import copy_file
from distutils.dir_util import copy_tree, mkpath

# this script scrapes all the data from the _Data folder from worm paparazzi 
# then transfers it into the regular holding in the Sutphin server

# this additionally makes a lookup table for easy checking of experiments that have already
# been created and easy to lookup

# Update settings
# if Set to True then the program will check if there is a newer version and update, or if file doesnt exist then will transfer it
# if false then it will overwrite everything 
update_files = True
# 50MB -> 50000000
max_file_size = 50000000

# get all the paths and directories of the 
# PATH_TO_WW = os.getcwd()
PATH_TO_WW = r"Z:\_Data"
# PATH_TO_SUTPHIN = "/Volumes/Sutphin server/Projects/Worm Paparazzi/Data"
PATH_TO_SUTPHIN = r"Z:\Projects\Worm Paparazzi\Data"
if os.path.isdir(PATH_TO_SUTPHIN) is not True:
    PATH_TO_SUTPHIN = r"Y:\Projects\Worm Paparazzi\Data"
PATH_TO_DIVISION_BASE = r"Z:\Worm_Paparazzi\Data_setup\Groupname_divisions.csv"
    
assert os.path.isdir(PATH_TO_SUTPHIN)
assert os.path.isdir(PATH_TO_WW)
assert os.path.isfile(PATH_TO_DIVISION_BASE)

#recursively get all the csv files from the _Data folder
EXT = "*.csv"
all_csv_files = [file
                 for path, subdir, files in os.walk(PATH_TO_WW)
                 for file in glob.glob(os.path.join(path, EXT))]

# get all the division paths for the data lookup table
division_csv_files = [ x for x in all_csv_files if "division" in x ]
# read in the base and columns for checking
base_division = pd.read_csv(PATH_TO_DIVISION_BASE)
base_columns = base_division.columns

print('Creating lookup table')
skip_counter = 0
for i in tqdm(range(len(division_csv_files))):
    try:
        this_division_df = pd.read_csv(division_csv_files[i])

        column_check_flag = sum((this_division_df.columns == base_columns)) == len(base_columns)

        if column_check_flag:
            this_path = os.path.normpath(division_csv_files[i])
            this_path = this_path.split(os.sep)

            this_experiment_overarching_name = this_path[-3]
            this_experiment_plate_name = this_path[-1][:-14]

            this_division_df = this_division_df.drop(columns='Well Location')
            this_division_df = this_division_df.drop_duplicates(keep='first') 

            this_division_df['Experiment name'] = this_experiment_overarching_name
            this_division_df['Plate name'] = this_experiment_plate_name

            if i == 0:
                large_division_dataframe = this_division_df
            else:
                large_division_dataframe = pd.concat([large_division_dataframe,this_division_df])

    except:
        skip_counter = skip_counter + 1
        print('skipping',division_csv_files[i])
print('Skipped', skip_counter, 'of', len(division_csv_files), 'possible plates')

large_division_dataframe.to_csv(os.path.join(os.path.split(PATH_TO_WW)[0],'_Processed_data_lookup.csv'), index = False )
large_division_dataframe.to_csv(os.path.join(os.path.split(PATH_TO_SUTPHIN)[0],'_Processed_data_lookup.csv'), index = False )

cleaned_csv_files = [ x for x in all_csv_files if "division" not in x ]
cleaned_csv_files = [ x for x in cleaned_csv_files if "Groupname.csv" not in x ]

for i in tqdm(range(len(cleaned_csv_files))):

    this_filepath = cleaned_csv_files[i]

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

