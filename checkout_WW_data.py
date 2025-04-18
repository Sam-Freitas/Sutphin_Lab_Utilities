import os, shutil
import glob
import tqdm
import pandas as pd
from numpy import cumsum, round
from pathlib import Path
from natsort import natsorted
from functools import reduce
import datetime

cutoff_date = "2022-09-15"
format_string = "%Y-%m-%d"  # Y: year, m: month, d: day
cutoff_date = datetime.datetime.strptime(cutoff_date,format_string)

WW_path = r"Z:\WormWatcher"
if not os.path.isdir(WW_path):
    WW_path = '/volume1/WormWatcher/WormWatcher'

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
    subfolders = get_subfolders(given_folder)

    all_names = []
    for this_subfolder in subfolders:
        temp = fast_scandir(this_subfolder)
        temp_names = [os.path.split(this_folder)[-1] for this_folder in temp]
        all_names.append(temp_names)
        pass

    all_names = flatten_list(all_names)
    unique_names = natsorted(list(set(all_names)))

    if '@eaDir' in unique_names:
        unique_names.remove('@eaDir')

    return unique_names


if __name__ == '__main__':

    column_names = ["Experiment name","path","first date","first datetime","space (GB)","space (TB)","Cumulative (TB)"]
    df = pd.DataFrame(columns = column_names)

    running_space_saving = 0

    WW_folders = natsorted([ f.path for f in os.scandir(WW_path) if f.is_dir() ])

    for i,this_folder in enumerate(tqdm.tqdm(WW_folders,total=len(WW_folders))):
        print('--------------------')
        print(this_folder)

        try:
            day_names = get_all_names_of_subfolders(this_folder)
            print(day_names[0],'---->',day_names[-1])

            first_datetime = datetime.datetime.strptime(day_names[0], format_string)
            first_timestamp = datetime.datetime.timestamp(first_datetime)
            
            print('-------------------------------> REMOVE ME : \t\t', os.path.split(this_folder)[-1])
            folder_size = get_size_of_folder(this_folder)
            print('-------------------------------> TO SAVE : \t\t', folder_size, 'GB')
            running_space_saving += folder_size
            print('-------------------------------> RUNNING SAVINGS : \t\t', round(running_space_saving,2), 'GB')

            df_running = [os.path.split(this_folder)[-1],this_folder,day_names[0],first_timestamp,folder_size,round(folder_size/1024,decimals=5),0]
            df.loc[i] = df_running

        except:
            print("----FAILED")

        # if i > 50:
        #     break
        # pass

    df = df.sort_values("first datetime",ascending=True)
    df["Cumulative (TB)"] = round(cumsum(df["space (TB)"].values),decimals=2)
    df.to_csv('/volume1/WormWatcher/python_dir/output_csv.csv', index=False)

    print('FINAL SPACE SAVINGS')
    print(round(running_space_saving,2), 'GB')
print("EOF")