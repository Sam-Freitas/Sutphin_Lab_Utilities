import os, glob, natsort, time
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

base_division = pd.read_csv(PATH_TO_DIVISION_BASE)
base_columns = base_division.columns

# print(base_division)

print('All paths have been verified')
print('Recursively looking up all .CSV files in', str(PATH_TO_WW))

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
for i, this_path in enumerate(tqdm(Path(PATH_TO_WW).rglob(EXT))):
    all_csv_files.append(str(this_path))
t_new = time.time() - t_new

# get all the division paths for the data lookup table
division_csv_files = [ x for x in all_csv_files if "division" in x ]
division_csv_files = natsort.natsorted(division_csv_files)
# read in the base and columns for checking
base_division = pd.read_csv(PATH_TO_DIVISION_BASE)
base_columns = base_division.columns

print('Creating lookup table')
skip_counter = 0
for i in tqdm(range(len(division_csv_files))):
    # try:
        this_division_df = pd.read_csv(division_csv_files[i])
        print(' ' + division_csv_files[i])

        this_path = os.path.normpath(division_csv_files[i])
        # print(this_path)
        this_path_split = this_path.split(os.sep)
        # print(this_path_split)
        this_path_experiment = os.path.join(*this_path_split[0:-2])
        # print(this_path_experiment)

        if platform == "linux" or platform == "linux2":
            this_path_experiment = '/' + this_path_experiment
            this_path_processed_data = glob.glob(os.path.join(this_path_experiment, "*.csv"))
        elif platform == "darwin":
            this_path_experiment = '/' + this_path_experiment
            this_path_processed_data = glob.glob(os.path.join(this_path_experiment, "*.csv"))
        elif platform == "win32":
            this_path_split[0] = this_path_split[0] + '\\'
            this_path_experiment = os.path.join(*this_path_split[0:-2])
            this_path_processed_data = glob.glob(os.path.join(this_path_experiment, "*.csv"))

        # print(this_path_processed_data)

        if len(this_division_df.columns) == len(base_columns):
            column_check_flag = sum((this_division_df.columns == base_columns)) == len(base_columns)
        else:
            column_check_flag = False

        if len(this_path_processed_data) == 1:
            processed_data_check_flag = True
        else:
            processed_data_check_flag = False

        # print(column_check_flag and processed_data_check_flag)

        if column_check_flag and processed_data_check_flag:
            # print('USING',division_csv_files[i])

            this_experiment_overarching_name = this_path_split[-3]
            this_experiment_plate_name = this_path_split[-1][:-14]

            this_experiment_data_df = pd.read_csv(this_path_processed_data[0])
            this_experiment_plate_name_idx = (this_experiment_data_df['Plate ID'].str.upper()==this_experiment_plate_name.upper()) # this islates the division from the rest of the data
            this_division_data_df = this_experiment_data_df[this_experiment_plate_name_idx]

            this_division_df = this_division_df.drop(columns='Well Location')
            this_division_df = this_division_df.drop_duplicates(keep='first') 

            N = []
            NC = []
            mean_lifepsan = []
            median_lifespan = []
            mean_healthspan = []
            median_healthspan = []
            time_between_egg_and_robot = []
            for j,each_division in enumerate(this_division_df['Groupname']):
                this_groupname_data = this_division_data_df[this_division_data_df['Groupname'] == each_division]
                this_groupname_data_noncensored = this_groupname_data[this_groupname_data['Death Detected']==1]

                time_between_egg_and_robot.append(
                    (datetime.strptime(this_division_df['robot date [yyyy-mm-dd]'][0],'%Y-%m-%d') 
                     - datetime.strptime(this_division_df['egg date'][0],'%Y-%m-%d')).days
                    )

                N.append(np.shape(this_groupname_data)[0])
                NC.append(np.shape(this_groupname_data)[0]-np.shape(this_groupname_data_noncensored)[0])
                if N[j] == NC[j]:
                    median_lifespan.append(None)
                    median_healthspan.append(None)
                    mean_lifepsan.append(None)
                    mean_healthspan.append(None)
                    continue
                median_lifespan.append(np.median(this_groupname_data_noncensored['Last day of observation']))
                median_healthspan.append(np.median(this_groupname_data_noncensored['Last day of health']))
                mean_lifepsan.append(np.mean(this_groupname_data_noncensored['Last day of observation']))
                mean_healthspan.append(np.mean(this_groupname_data_noncensored['Last day of health']))

            this_division_df['Experiment name'] = this_experiment_overarching_name
            this_division_df['Plate name'] = this_experiment_plate_name
            this_division_df['N'] = N
            this_division_df['NC'] = NC
            this_division_df['Median Lifespan'] = median_lifespan
            this_division_df['Median Healthspan'] = median_healthspan
            this_division_df['Mean Lifespan'] = mean_lifepsan
            this_division_df['Mean Healthspan'] = mean_healthspan
            this_division_df['Egg to Robot time [d]'] = time_between_egg_and_robot

            if i == 0:
                large_division_dataframe = this_division_df
            else:
                large_division_dataframe = pd.concat([large_division_dataframe,this_division_df])

            if this_division_df.empty:# or this_division_df.isnull().all():
                pass
                # print(this_path_processed_data[0], '-----------', this_experiment_plate_name.upper())
        else:
            skip_counter = skip_counter + 1
            print(' skipping',division_csv_files[i])

print('Skipped', skip_counter, 'of', len(division_csv_files), 'possible plates')

a = large_division_dataframe.copy() # sort the dataframe with a temporary 
a['d'] = pd.to_datetime(a['egg date'])
a = a.sort_values(by=['d','Plate name','Groupname'],ascending=[False,True,True])
a = a.drop(columns = 'd')

large_division_dataframe = a

large_division_dataframe.to_csv(os.path.join(os.path.split(PATH_TO_WW)[0],'_Processed_data_lookup.csv'), index = False )
large_division_dataframe.to_csv(os.path.join(os.path.split(PATH_TO_SUTPHIN)[0],'_Processed_data_lookup.csv'), index = False )

# get rid of unnecessary csvs
cleaned_csv_files = [ x for x in all_csv_files if "division" not in x ]
cleaned_csv_files = [ x for x in cleaned_csv_files if "Groupname.csv" not in x ]
 
for i in tqdm(range(len(cleaned_csv_files))):

    this_filepath = cleaned_csv_files[i]

    # get filename of csv
    file_name = Path(this_filepath).stem
    # get name of experiment 
    this_dir = os.path.dirname(this_filepath)
    this_dir_name = Path(this_dir).stem
    # print('')
    print(this_dir_name)
    # make a new path 
    new_dir_path = os.path.join(PATH_TO_SUTPHIN,this_dir_name)
    # print(new_dir_path)

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

