import os
import glob
import numpy as np
import shutil
from pathlib import Path
from distutils.dir_util import copy_tree

PATH_TO_WW = "Z:\_Data"
PATH_TO_SUTPHIN = "Y:\Projects\Worm Paparazzi\Data"
EXT = "*.csv"
all_csv_files = [file
                 for path, subdir, files in os.walk(PATH_TO_WW)
                 for file in glob.glob(os.path.join(path, EXT))]

all_csv_files2 = [ x for x in all_csv_files if "division" not in x ]
all_csv_files2 = [ x for x in all_csv_files2 if "Groupname" not in x ]

for i,this_filepath in enumerate(all_csv_files2):

    file_name = Path(this_filepath).stem

    print(file_name)

    this_dir = os.path.dirname(this_filepath)

    activity_path = os.path.join(this_dir,"activity_groupings")

    new_dir_path = os.path.join(PATH_TO_SUTPHIN,file_name)

    new_activity_path = os.path.join(PATH_TO_SUTPHIN,file_name,"activity_groupings")

    new_path = os.path.join(new_dir_path,file_name + ".csv")

    if not os.path.exists(new_dir_path):
        os.mkdir(new_dir_path)

    shutil.copy(this_filepath,new_path)


    try: 
        copy_tree(activity_path, new_activity_path)
    except:
        print(file_name, " Activity not found")

