import sys
import os, glob, shutil, copy,time
from natsort import natsorted
import numpy as np
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QDialog, QLabel, 
    QProgressBar, QGridLayout, QCheckBox, QDialogButtonBox
)    
from PyQt6.QtGui import QFont
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor, QBrush

from _data_utils import *

def setup_func():

    os.makedirs('_Data_fixes/_Data_copy',exist_ok=True)
    shutil.rmtree('_Data_fixes/_Data_copy')
    os.makedirs('_Data_fixes/_Data_copy',exist_ok=True)

if __name__ == "__main__":

    file_name = os.path.splitext(os.path.basename(__file__))[0]
    log_path = 'log_' + file_name + '.txt'
    
    try:
        os.remove(log_path)
        write_log("restarted LOGGING",log_name=log_path)
    except:
        write_log("New LOGGING",log_name=log_path)

    setup_func()

    app = QApplication(sys.argv)

    overarching_Data_path = r"Z:\_Data"
    assert(os.path.isdir(overarching_Data_path))
    write_log("found _Data path:",log_name=log_path)
    write_log(overarching_Data_path,log_name=log_path)

    output_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_copy"

    # progress bar time(!)
    root_progressbar, progress_bar, progress_bar_label = create_progress_window()
    update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_groupname_csvs = natsorted(find_files(overarching_Data_path, file_extension='.csv', filter='Groupname.csv', filter2 = None))

    for i,this_found_groupname_csv in enumerate(found_groupname_csvs):

        try:
            # get the name and update the 
            this_exp_name = get_experiment_name(this_found_groupname_csv)
            write_log(this_exp_name,log_name=log_path)
            progress_bar_text = this_exp_name+'-'*(50-len(this_exp_name))+str(i+1)+'/'+str(len(found_groupname_csvs))
            update_progress_bar(progress_bar,progress_bar_label,current_iteration=i+1,total=len(found_groupname_csvs),
                text=progress_bar_text)
            
            # Groupname find, get new path, and the copy
            this_groupname = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='Groupname.csv')[0]
            this_groupname_export = os.path.join(output_path,*get_path_parts(this_groupname)[-3:])
            os.makedirs(os.path.split(this_groupname_export)[0],exist_ok=True)
            shutil.copy2(this_groupname,this_groupname_export)

            # divisions find, get new path, and then copy
            this_divisions = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='_divisions.csv')
            for each_division in this_divisions:
                this_div_export = os.path.join(output_path,*get_path_parts(each_division)[-3:])
                os.makedirs(os.path.split(this_div_export)[0],exist_ok=True)
                shutil.copy2(each_division,this_div_export)

            # exported dat afind get new path and copy over
            this_exported_data = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='')
            for temp in [this_groupname] + this_divisions:
                this_exported_data.remove(temp)
            this_exported_data = this_exported_data[0]
            this_exp_data_export = os.path.join(output_path,*get_path_parts(this_exported_data)[-2:])
            os.makedirs(os.path.split(this_exp_data_export)[0],exist_ok=True)
            shutil.copy2(this_exported_data,this_exp_data_export)

        except:
            write_log('--------- FAILED',log_name=log_path)

    shutil.make_archive(output_path,'zip',output_path)
    write_log('asdfasdf',log_name=log_path)