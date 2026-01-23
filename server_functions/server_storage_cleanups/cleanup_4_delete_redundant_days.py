import os, shutil, sys
import glob
import tqdm
import pandas as pd
# import numpy as np
from numpy import round
import numpy as np
from pathlib import Path
from natsort import natsorted
from functools import reduce
import datetime

## this is the second step in cleaning up the server 
## associated the found folders with a processed lifspan

cutoff_date = "2024-01-01"
format_string = "%Y-%m-%d"  # Y: year, m: month, d: day
cutoff_date = datetime.datetime.strptime(cutoff_date,format_string)
max_number_days_fallback = 60
lifespan_additional_delta = 2
avg_GB_per_day = 0.5

WW_path = r"Z:\WormWatcher"
if not os.path.isdir(WW_path):
    WW_path = '/volume1/WormWatcher/WormWatcher'

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

def get_size_of_folder(root_directory,decimals = 2):

    # give this a path not a Path object
    root_directory = Path(root_directory)
    folder_size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

    out = folder_size/(2**30) # returns in GB

    return round(folder_size/(2**30),decimals)

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

    # this is for reference only from the previous step
    # df_column_names = ['days to remove','paths to remove','space savings']

    df = pd.read_csv(os.path.join(output_path,'cleanup_server3.csv'),index_col=False)
    print('FOUND COLUMNS:\n', list(df.columns))


    input_str = "\n\n\n\nAre you sure you want to run this?\nIT WILL delete terabytes of data with no way to replace them\nCONFRIM ---- yes(Y) - no(N)"
    user_input = input(input_str)

    if user_input != 'Y':
        print("\n\nUser exit")
        sys.exit(0)
    else:

        estimated_space_savings = round(np.sum(df['space savings'])/1024,2)

        input_str2 = "\n\n\n\nThis will delete " + str(estimated_space_savings) + "TB of data \nCONFRIM ---- yes(Y) - no(N)"
        user_input2 = input(input_str2)

        if user_input2 != 'Y':
            print("\n\nUser exit")
            sys.exit(0)

    WW_experiments_paths = list(df["path"])
    WW_experiment_name = list(df["Experiment name"])

    for i,(this_WW_exp_name,this_WW_exp_path) in enumerate(tqdm.tqdm(zip(WW_experiment_name,WW_experiments_paths),total=len(WW_experiment_name))):

        print('\n--------------------\n')
        print(this_WW_exp_name)
        # print(this_WW_exp_name,this_WW_exp_path)

        if df["continue3"][i]:

            # get the paths from the csv as a string and transform them back into a list of paths
            paths_to_delete = df.iat[i,df.columns.get_loc('paths to remove')]
            if paths_to_delete == '[]':
                paths_to_delete = None
            else:
                paths_to_delete = paths_to_delete.replace("'",'').replace("[",'').replace("]",'')
                paths_to_delete = paths_to_delete.split(', ')
                paths_to_delete = natsorted(paths_to_delete)

            days_to_remove = df.iat[i,df.columns.get_loc('days to remove')]
            if days_to_remove == '[]':
                days_to_remove = None
            else:
                days_to_remove = days_to_remove.replace("'",'').replace("[",'').replace("]",'')
                days_to_remove = days_to_remove.split(', ')
                days_to_remove = natsorted(days_to_remove)

            print(os.path.commonprefix(paths_to_delete))
            print(days_to_remove)

            continue_to_delete_flag = paths_to_delete and days_to_remove
            if continue_to_delete_flag:
                print('--- deleting')
                for j,this_folder_to_delete in enumerate(paths_to_delete):
                    print(j,this_folder_to_delete)
                    files_to_delete = glob.glob(os.path.join(this_folder_to_delete,'*'))

                    if files_to_delete:
                        for this_file_to_delete in files_to_delete:
                            os.remove(this_file_to_delete)
            ## this is to only be run when absolutely sure that we want to delete data

            pass
        pass
    pass