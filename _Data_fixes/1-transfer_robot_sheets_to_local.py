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

    os.makedirs('_Data_fixes/robot_sheets',exist_ok=True)
    shutil.rmtree('_Data_fixes/robot_sheets')
    os.makedirs('_Data_fixes/robot_sheets',exist_ok=True)

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

    overarching_Robot_path = r"Y:\Reference\Robot Experiment Sheets"
    assert(os.path.isdir(overarching_Robot_path))
    write_log("found _Data path:",log_name=log_path)
    write_log(overarching_Robot_path,log_name=log_path)

    output_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\robot_sheets"

    # progress bar time(!)
    root_progressbar, progress_bar, progress_bar_label = create_progress_window()
    update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_robot_sheets_pdf = natsorted(find_files(overarching_Robot_path, file_extension='.pdf', filter='', filter2 = None))

    for i,this_found_robot_sheet in enumerate(found_robot_sheets_pdf):

        try:
            # get the name and update the 
            this_sheet_name = os.path.splitext(os.path.split(this_found_robot_sheet)[-1])[0]
            write_log(this_sheet_name,log_name=log_path)
            progress_bar_text = this_sheet_name+'-'*(50-len(this_sheet_name))+str(i+1)+'/'+str(len(found_robot_sheets_pdf))
            update_progress_bar(progress_bar,progress_bar_label,current_iteration=i+1,total=len(found_robot_sheets_pdf),
                text=progress_bar_text)

            this_sheet_export = os.path.join(output_path,os.path.split(this_found_robot_sheet)[-1])

            shutil.copy2(this_found_robot_sheet,this_sheet_export)

        except:
            write_log('--------- FAILED',log_name=log_path)

    write_log('asdfasdf',log_name=log_path)