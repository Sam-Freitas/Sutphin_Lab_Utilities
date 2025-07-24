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

if __name__ == "__main__":
    
    log_path = 'log_batch_add_new_conditions_to_data.txt'

    duplicates_name = []
    duplicates_df = []

    try:
        os.remove(log_path)
        write_log("restarted LOGGING",log_name=log_path)
    except:
        write_log("New LOGGING",log_name=log_path)

    app = QApplication(sys.argv)

    # load in the data copy from the local drive
    overarching_Data_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_copy"
    assert(os.path.isdir(overarching_Data_path))
    write_log("found _Data path:",log_name=log_path)
    write_log(overarching_Data_path,log_name=log_path)

    # output path
    output_path = overarching_Data_path

    # load in the frozen stock keys that we use 
    frozen_stock_KEY = pd.read_excel(r'_Data_fixes\Sutphin Worm Frozen Stock AZ.xlsx',sheet_name=1,keep_default_na=False,na_values=[])
    strain_genotype_lookup = frozen_stock_KEY.copy()

    # make a copy of the strains as a lower() for ease of matching
    strain_genotype_lookup_lower = frozen_stock_KEY.copy().map(str).map(str.lower)

    # progress bar time(!)
    root_progressbar, progress_bar, progress_bar_label = create_progress_window()
    update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_groupname_csvs = natsorted(find_files(overarching_Data_path, file_extension='.csv', filter='Groupname.csv', filter2 = None))
    write_log('',log_name=log_path)

    for i,this_found_groupname_csv in enumerate(found_groupname_csvs):

        continue_flag = False
    
