import os, shutil
import glob
import tqdm
import pandas as pd
# import numpy as np
from numpy import cumsum, round, asarray
from pathlib import Path
from natsort import natsorted
from functools import reduce
import datetime

cutoff_date = "2024-01-01"
format_string = "%Y-%m-%d"  # Y: year, m: month, d: day
cutoff_date = datetime.datetime.strptime(cutoff_date,format_string)

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

def get_size_of_folder(root_directory):

    # give this a path not a Path object
    root_directory = Path(root_directory)
    folder_size = sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())

    out = folder_size/(2**30) # returns in GB

    return round(folder_size/(2**30),2)

def get_all_names_of_subfolders(given_folder):
    subfolders = get_subfolders(given_folder)

    all_names = []
    all_data_folders = []
    for this_subfolder in subfolders:
        temp = fast_scandir(this_subfolder)
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

    ## what would be smart is to find where the processed data csv for each experiment 
    ## then find the last day an animal was alive 
    ## then have a variable days_maximum 

    column_names = ["Experiment name","path","first date","first datetime","Num Days","days_maximum","Num Days Over","space (GB)","space (TB)","Cumulative (TB)"]
    df = pd.DataFrame(columns = column_names)

    days_maximum = 30

    running_space_saving = 0

    WW_folders = natsorted([ f.path for f in os.scandir(WW_path) if f.is_dir() ])
    Data_folders = natsorted([ f.path for f in os.scandir(processed_data_path) if f.is_dir() ])

    for i,this_folder in enumerate(tqdm.tqdm(WW_folders,total=len(WW_folders))):
        print('--------------------')
        print(this_folder)

        name_of_experiment = os.path.split(this_folder)[-1]
        boolean_list_matcher = [name_of_experiment.lower() == os.path.split(temp_this_Data)[-1].lower() for temp_this_Data in Data_folders]

        # find the final day of lifespan for this experiment 
        # and set it to the max number of days
        if any(boolean_list_matcher):
            chosen_data_path = str(asarray(Data_folders)[asarray(boolean_list_matcher)][0])

            chosen_data_csv_path = os.path.join(chosen_data_path,os.path.split(chosen_data_path)[-1] + '.csv')
            if os.path.isfile(chosen_data_csv_path):
                temp_data_csv = pd.read_csv(chosen_data_csv_path)
                days_maximum = int(temp_data_csv['Last day of observation'].max())
                days_maximum = days_maximum + 1
        else:
            days_maximum = 30

        # find the number of days in each subfolder 
        try:
            day_names,subfolder_paths,all_data_folders = get_all_names_of_subfolders(this_folder)
            print(day_names[0],'---->',day_names[-1])

            days_per_subfolder = [len(temp) for temp in all_data_folders]

            first_datetime = datetime.datetime.strptime(day_names[0], format_string)
            first_timestamp = datetime.datetime.timestamp(first_datetime)

            num_days = max(days_per_subfolder)

            # reset the defaults for each loop
            too_many_days_flag = False
            num_days_over = 0

            # determine of there are too many days
            # and if so get the size of each folder
            if num_days > days_maximum:
                too_many_days_flag = True

                data_folders_that_are_extra = []
                running_space_saving_Nday = 0

                for this_days_collection in all_data_folders:
                    this_days_collection = natsorted(this_days_collection)

                    if len(this_days_collection) > days_maximum:
                        extra_days_data_folders = this_days_collection[days_maximum:]
                        data_folders_that_are_extra.append(extra_days_data_folders)
                        for this_data_folder in extra_days_data_folders:
                            running_space_saving_Nday += get_size_of_folder(this_data_folder)

                num_days_over = num_days - days_maximum
                print('over by N:', num_days-days_maximum, "days")

            if too_many_days_flag:
                print('-------------------------------> REMOVE ME : \t\t', os.path.split(this_folder)[-1])
                num_days = num_days
                print('-------------------------------> NUMBER OF OVER : \t', num_days-days_maximum)
                folder_size = running_space_saving_Nday
                print('-------------------------------> TO SAVE : \t\t', round(folder_size,2), 'GB')
                running_space_saving += folder_size
                print('-------------------------------> RUNNING SAVINGS : \t\t', round(running_space_saving,2), 'GB')
            else:
                folder_size = 0


            df_running = [os.path.split(this_folder)[-1],this_folder,day_names[0],first_timestamp,num_days,days_maximum,num_days_over,round(folder_size,2),round(folder_size/1024,decimals=5),0]
            df.loc[i] = df_running

        except:
            print("----FAILED")

        # if i > 10:
        #     break
        # pass

    df = df.sort_values("first datetime",ascending=True)
    df["Cumulative (TB)"] = round(cumsum(df["space (TB)"].values),decimals=2)
    df.to_csv('/volume1/WormWatcher/python_dir/output_Ndays_removal_csv.csv', index=False)

    print('FINAL SPACE SAVINGS')
    print(round(running_space_saving,2), 'GB')
print("EOF")