import numpy as np
import pandas as pd
import os, datetime, time
from glob import glob
from natsort import natsorted
from tqdm import tqdm

path_to_lookup = r"Y:\Projects\Worm Paparazzi\_Processed_data_lookup.csv"

def find_files(folder_path, file_extension='.png', filter='fluorescent_data', filter2 = None):
    """
    Recursively finds and returns all files with the specified extension in the given folder,
    only if the filter string is contained within the file path.

    Args:
        folder_path (str): The path to the folder to search.
        file_extension (str): The file extension to search for (default is '.png').
        filter (str): The filter string that must be in the file path to be included in the result (default is 'fluorescent_data').

    Returns:
        list: A list of file paths that match the specified extension and contain the filter string.
    """
    found_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(file_extension.lower()) and filter in os.path.join(root, file):
                found_files.append(os.path.join(root, file))

    # secondary optional filter
    if filter2:
        found_files2 = []
        for file in found_files:
            if filter2 in file:
                found_files2.append(file)
        return found_files2
    else:
        return found_files

def flatten_list(lst):
    return reduce(lambda x,y: x+y, lst)

def unique_list(lst):
    return natsorted(list(set(lst)))

if __name__ == "__main__":

    processed_data_LUT = pd.read_csv(path_to_lookup,index_col=False)

    groupnames = list(processed_data_LUT["Groupname"])
    compounds = list(processed_data_LUT['Compound [XmM Name]'])
    bacterial_strains = list(processed_data_LUT["Bacterial Strains"])


    exclude_list = ['(rnai)','gls','0ug/ml cholesterol','gr','daf','skn','pmk','sun01','100','200','etoh','op50']

    controls_idxs = []
    controls_names = []
    controls_compounds = []
    controls_bacteria = []
    for i in range(len(groupnames)):
        groupnames[i] = groupnames[i].lower()
        bacterial_strains[i] = bacterial_strains[i].lower()
        if ('control' in groupnames[i]) or ('0m' in groupnames[i][0:2]) or ('0u' in groupnames[i][0:2]):

            continue_flag = True
            for this_exclude in exclude_list:
                if (this_exclude in groupnames[i]) or (this_exclude in bacterial_strains[i]):
                    continue_flag = False
                    break
            
            if continue_flag:
                controls_idxs.append(i)
                controls_names.append(groupnames[i])
                controls_compounds.append(compounds[i])
                controls_bacteria.append(bacterial_strains[i])
   
    unique_control_names = unique_list(controls_names)

    for this_name in unique_control_names:
        print(this_name)

    print('asdfasdf')