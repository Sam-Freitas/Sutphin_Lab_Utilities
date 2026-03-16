import os, shutil, difflib
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
# the cutoff date doesnt do anything yet
# should be changed to more heavily purge date that isnt processed
# and falls behind the cutoff date
max_number_days_fallback = 60
lifespan_additional_delta = 3
min_number_days_fallback = 20-lifespan_additional_delta
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

    df_column_names = ['matched','found _Data csv','max lifespan','max allowed days','extra days','space savings GB','last allowed date','total TB','continue3']

    df = pd.read_csv(os.path.join(output_path,'cleanup_server1.csv'),index_col=False)
    print('FOUND COLUMNS:\n', list(df.columns))

    df[df_column_names] = ''

    Data_folders = natsorted([ f.path for f in os.scandir(processed_data_path) if f.is_dir() ])
    Data_folders_names = [os.path.split(temp_this_Data)[-1].lower() for temp_this_Data in Data_folders]

    WW_experiments_paths = list(df["path"])
    WW_experiment_name = list(df["Experiment name"])

    for i,(this_WW_exp_name,this_WW_exp_path) in enumerate(tqdm.tqdm(zip(WW_experiment_name,WW_experiments_paths),total=len(Data_folders))):
        
        print('--------------------')
        print(this_WW_exp_name,this_WW_exp_path)

        if df["continue2"][i]:

            print('continued:')

            plates_in_experiment = get_subfolders(this_WW_exp_path)
            num_plates_in_experiment = len(plates_in_experiment)

            boolean_list_matcher = [this_WW_exp_name.lower() == temp_this_Data for temp_this_Data in Data_folders_names]

            if any(boolean_list_matcher):

                df.iat[i,df.columns.get_loc('matched')] = True
                print('found processed data match')

                chosen_data_path = str(np.asarray(Data_folders)[np.asarray(boolean_list_matcher)][0])
                chosen_data_csv_path = os.path.join(chosen_data_path,os.path.split(chosen_data_path)[-1] + '.csv')
                if os.path.isfile(chosen_data_csv_path):
                    print('found lifespan csv')

                    df.iat[i,df.columns.get_loc('found _Data csv')] = chosen_data_csv_path

                    temp_data_csv = pd.read_csv(chosen_data_csv_path)
                    max_lifespan = int(temp_data_csv['Last day of observation'].max())
                    max_lifespan = max([min_number_days_fallback,max_lifespan]) # make sure its not too small
                    df.iat[i,df.columns.get_loc('max lifespan')] = max_lifespan

                    days_maximum = max_lifespan + lifespan_additional_delta
                    df.iat[i,df.columns.get_loc('max allowed days')] = days_maximum

                    first_day_datetime = datetime.datetime.strptime(df["first date"][i],format_string)
                    calculated_last_datetime = first_day_datetime + datetime.timedelta(days = days_maximum)

                    extra_days = int(df.iat[i,df.columns.get_loc('delta days')]) - days_maximum

                    num_days_to_keep = days_maximum
                    pass
            else:
                # this will attempt to find the closest match to whatever is going on
                # 1 finds easy matches 
                # 2 determines if the processed data is correct
                # 2.i or if there are multiple parts spread out

                matches = difflib.get_close_matches(this_WW_exp_name.lower(), Data_folders_names, 5, 0.95)
                print(matches)
                piecewise_matches = [this_WW_exp_name.lower() in temp for temp in Data_folders_names]

                if any(piecewise_matches):
                    # this is for the pt1 pt2 pt3

                    potential_matches = np.asarray(Data_folders)[np.asarray(piecewise_matches)]
                    potential_matches = potential_matches.tolist()

                    potential_matches_csv = flatten_list([glob.glob(os.path.join(temp,'*.csv')) for temp in potential_matches])

                    df.iat[i,df.columns.get_loc('found _Data csv')] = potential_matches_csv

                    temp_data_list = [pd.read_csv(temp) for temp in potential_matches_csv]
                    temp_data_csv = pd.concat(temp_data_list,ignore_index=True)
                    max_lifespan = int(temp_data_csv['Last day of observation'].max())
                    max_lifespan = max([min_number_days_fallback,max_lifespan]) # make sure its not too small

                    df.iat[i,df.columns.get_loc('max lifespan')] = max_lifespan
                    days_maximum = max_lifespan + lifespan_additional_delta
                    df.iat[i,df.columns.get_loc('max allowed days')] = days_maximum
                    first_day_datetime = datetime.datetime.strptime(df["first date"][i],format_string)
                    calculated_last_datetime = first_day_datetime + datetime.timedelta(days = days_maximum)
                    extra_days = int(df.iat[i,df.columns.get_loc('delta days')]) - days_maximum
                    num_days_to_keep = days_maximum

                    pass

                elif matches:

                    closest_match = matches[0]

                    if closest_match[-2:] == this_WW_exp_name[-2:]:
                        print('Matched!')
                        # this is for when there is a slight misspelling or something else small

                        boolean_list_matcher = [temp == closest_match for temp in Data_folders_names]
                        potential_matches = np.asarray(Data_folders)[np.asarray(boolean_list_matcher)]
                        potential_matches = potential_matches.tolist()

                        potential_matches_csv = flatten_list([glob.glob(os.path.join(temp,'*.csv')) for temp in potential_matches])

                        df.iat[i,df.columns.get_loc('found _Data csv')] = potential_matches_csv

                        temp_data_list = [pd.read_csv(temp) for temp in potential_matches_csv]
                        temp_data_csv = pd.concat(temp_data_list,ignore_index=True)
                        max_lifespan = int(temp_data_csv['Last day of observation'].max())
                        max_lifespan = max([min_number_days_fallback,max_lifespan]) # make sure its not too small
                        
                        df.iat[i,df.columns.get_loc('max lifespan')] = max_lifespan
                        days_maximum = max_lifespan + lifespan_additional_delta
                        df.iat[i,df.columns.get_loc('max allowed days')] = days_maximum
                        first_day_datetime = datetime.datetime.strptime(df["first date"][i],format_string)
                        calculated_last_datetime = first_day_datetime + datetime.timedelta(days = days_maximum)
                        extra_days = int(df.iat[i,df.columns.get_loc('delta days')]) - days_maximum
                        num_days_to_keep = days_maximum

                        pass
                    else:
                        # fallback
                        # if nothing could be found then defaults
                        df.iat[i,df.columns.get_loc('max allowed days')] = max_number_days_fallback
                        extra_days = int(df.iat[i,df.columns.get_loc('delta days')]) - max_number_days_fallback
                        num_days_to_keep = max_number_days_fallback
                else:
                    # fallback
                    # if nothing could be found then defaults
                    df.iat[i,df.columns.get_loc('max allowed days')] = max_number_days_fallback
                    extra_days = int(df.iat[i,df.columns.get_loc('delta days')]) - max_number_days_fallback
                    num_days_to_keep = max_number_days_fallback
            
            extra_days = max([0,extra_days])
            df.iat[i,df.columns.get_loc('extra days')] = extra_days

            date_to_keep_up_to = datetime.datetime.strptime(df.iat[i,df.columns.get_loc('first date')],format_string) + datetime.timedelta(days=num_days_to_keep)
            df.iat[i,df.columns.get_loc('last allowed date')] = date_to_keep_up_to.strftime(format_string)
            
            df.iat[i,df.columns.get_loc('space savings GB')] = round(extra_days*num_plates_in_experiment*avg_GB_per_day,2)

            df.iat[i,df.columns.get_loc('continue3')] = True

            pass
        else:
            df.iat[i,df.columns.get_loc('continue3')] = False

    temp = np.asarray(df['space savings GB'])
    indices_to_delete = np.where(temp == '')
    result = np.delete(temp, indices_to_delete)

    df.iat[0,df.columns.get_loc('total TB')] = round(np.sum(result)/1000,2)

    df.to_csv(os.path.join(output_path,'cleanup_server2.csv'), index=False)

    print("EOF")