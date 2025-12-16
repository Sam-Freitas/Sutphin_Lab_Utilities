import os, shutil
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

    df_column_names = ['days to remove','paths to remove','space savings']

    df = pd.read_csv(os.path.join(output_path,'cleanup_server2.csv'),index_col=False)
    print('FOUND COLUMNS:\n', list(df.columns))

    df[df_column_names] = ''

    WW_experiments_paths = list(df["path"])
    WW_experiment_name = list(df["Experiment name"])

    for i,(this_WW_exp_name,this_WW_exp_path) in enumerate(tqdm.tqdm(zip(WW_experiment_name,WW_experiments_paths),total=len(WW_experiment_name))):

        print('--------------------')
        print(this_WW_exp_name,this_WW_exp_path)

        if df["continue3"][i]:

            last_date = df.iat[i,df.columns.get_loc('last date')]
            last_allowed_date = df.iat[i,df.columns.get_loc('last allowed date')]

            start_date = datetime.datetime.strptime(last_allowed_date,format_string)
            end_date = datetime.datetime.strptime(last_date,format_string)

            delta = end_date - start_date   # returns timedelta

            day_list_to_remove = []
            for j in range(delta.days + 1):
                day = start_date + datetime.timedelta(days=j)
                day_list_to_remove.append(day.strftime(format_string))

            df.iat[i,df.columns.get_loc('days to remove')] = day_list_to_remove

            ##### add functions here where it finds the 
            # associated paths from each of the experiment plates
            # add appends them into a large list 
            # that would be read later for deletions 

            unique_names, subfolders, all_data_folders = get_all_names_of_subfolders(df.loc[i]['path'])

            all_data_folders_flattened = flatten_list(all_data_folders)

            temp = [False]*len(all_data_folders_flattened)
            for j,this_subsubdata_folder in enumerate(all_data_folders_flattened):
                for jj,this_day_list_to_remove in enumerate(day_list_to_remove):
                    if this_day_list_to_remove in this_subsubdata_folder:
                        # print(this_day_list_to_remove,this_subsubdata_folder)
                        temp[j] = True
                        break

            array_of_subfolders = np.asarray(all_data_folders_flattened)[temp]
            list_of_subfolders = list(flatten_list(list(array_of_subfolders)))

            df.iat[i,df.columns.get_loc('paths to remove')] = list_of_subfolders

            total_size = round(sum([get_size_of_folder(this_folder) for this_folder in list_of_subfolders]),2)

            df.iat[i,df.columns.get_loc('space savings')] = total_size

            pass

    df.to_csv(os.path.join(output_path,'cleanup_server3.csv'), index=False)