import os, shutil
import glob
import tqdm
import pandas as pd
# import numpy as np
from numpy import round
from pathlib import Path
from natsort import natsorted
from functools import reduce
import datetime

## this is the first step in cleaning up the server 

cutoff_date = "2024-01-01"
format_string = "%Y-%m-%d"  # Y: year, m: month, d: day
cutoff_date = datetime.datetime.strptime(cutoff_date,format_string)

WW_path = r"Z:\WormWatcher_cleanup_test"
if not os.path.isdir(WW_path):
    WW_path = '/volume1/WormWatcher/WormWatcher_cleanup_test'

processed_data_path = r"Z:\_Data"
if not os.path.isdir(processed_data_path):
    processed_data_path = '/volume1/WormWatcher/_Data'

def flatten_list(lst):
    return reduce(lambda x,y: x+y, lst)

def fast_scandir(dirname):
    subfolders= [f.path for f in os.scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders

def get_subfolders(given_folder):
    subfolders = [ f.path for f in os.scandir(given_folder) if f.is_dir() ]
    return subfolders 

def get_size_of_folder(root_directory):

    # give this a path not a Path object
    root_directory = Path(root_directory)
    folder_size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

    out = folder_size/(2**30) # returns in GB

    return round(folder_size/(2**30),2)

def get_all_names_of_subfolders(given_folder):
    subfolders = natsorted(get_subfolders(given_folder))

    all_names = []
    all_data_folders = []
    for this_subfolder in subfolders:
        print('Scanning:',this_subfolder)
        # temp = fast_scandir(this_subfolder)
        temp = natsorted(get_subfolders(this_subfolder))
        all_data_folders.append(temp)
        temp_names = [os.path.split(this_folder)[-1] for this_folder in temp]
        all_names.append(temp_names)
        pass

    # all_data_folders = flatten_list(all_data_folders)

    all_names = flatten_list(all_names)
    unique_names = natsorted(list(set(all_names)))

    if '@eaDir' in unique_names:
        unique_names.remove('@eaDir')

    return unique_names, subfolders, all_data_folders


if __name__ == '__main__':

    output_path = os.path.dirname(os.path.abspath(__file__))

    known_bad_experiments = ["CoolTerm Libs","CoolTerm Resources",".vscode","Documents","Dependents",
                            "4","ROI_images_24","ROI_images_WM","ROI_images_WM_new",
                            "Samples","Scripts","Test Scripts",
                            "WW","backups","blanks","calibration","logs","models","old_params",
                            "New folder","New folder (2)","New folder (3)","New folder (4)",
                            "WWAnalyzer","WWAnalyzer 2019-06-04 BETA","WWConfig","WWConfigPy","WWCore","WWPythonSupplements",
                            "old_params_05-Feb-2019_10-28-50","old_params_06-Mar-2019_15-23-58","old_params_21-May-2019_12-38-39"]

    column_names = ["Experiment name","path","continue1","first timestamp","first date","last date","num days","delta days","continue2"]
    df = pd.DataFrame(columns = column_names)

    WW_experiments_paths = natsorted([ f.path for f in os.scandir(WW_path) if f.is_dir() ])
    WW_experiment_name = [os.path.split(temp)[-1] for temp in WW_experiments_paths]

    df["Experiment name"] = WW_experiment_name
    df["path"] = WW_experiments_paths

    continue_column = []
    for i,this_exp_name in enumerate(WW_experiment_name):
        if this_exp_name in known_bad_experiments:
            continue_column.append(False)
        else:
            continue_column.append(True)
    df["continue1"] = continue_column

    df.to_csv(os.path.join(output_path,'cleanup_server0.csv'), index=False)

    for i,(this_folder,this_exp_name) in enumerate(tqdm.tqdm(zip(WW_experiments_paths,WW_experiment_name),total=len(WW_experiments_paths))):
        
        print('--------------------')
        print(this_folder)

        if continue_column[i]:
            print("Continuing")

            # find the number of days in each subfolder 
            try:
                day_names,subfolder_paths,all_data_folders = get_all_names_of_subfolders(this_folder)
                print(day_names[0],'---->',day_names[-1])

                days_per_subfolder = [len(temp) for temp in all_data_folders]

                # get the first and last days 
                first_datetime = datetime.datetime.strptime(day_names[0], format_string)
                last_datetime = datetime.datetime.strptime(day_names[-1], format_string)
                first_timestamp = datetime.datetime.timestamp(first_datetime)

                df.iat[i,df.columns.get_loc('first timestamp')] = first_timestamp
                df.iat[i,df.columns.get_loc('first date')] = day_names[0]
                df.iat[i,df.columns.get_loc('last date')] = day_names[-1]

                num_days = max(days_per_subfolder)
                df.iat[i,df.columns.get_loc('num days')] = num_days

                delta_days = last_datetime-first_datetime + datetime.timedelta(days = 1)
                df.iat[i,df.columns.get_loc('delta days')] = delta_days.days

                df.iat[i,df.columns.get_loc('continue2')] = True
            except:
                df.iat[i,df.columns.get_loc('continue2')] = False
                print("----FAILED")
        else:
            df.iat[i,df.columns.get_loc('continue2')] = False

    df.to_csv(os.path.join(output_path,'cleanup_server1.csv'), index=False)
print("EOF")