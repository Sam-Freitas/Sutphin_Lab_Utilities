import sys
import os, glob, shutil, copy
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

    os.makedirs('temp_data',exist_ok=True)
    os.makedirs(os.path.join('temp_data','exported_data'), exist_ok=True)
    shutil.rmtree(os.path.join('temp_data','exported_data'))

if __name__ == "__main__":

    setup_func()

    app = QApplication(sys.argv)
    editor = CSVEditor()
    editor.resize(1000, 600)
    editor.show()
    app.exec()

    print('finishing and exporting changes---------------')   
    export_path = get_export_path()

    print('loading groupnames\n')
    groups_that_changed, updated_groupname_df, previous_groupname_df, previous_groupname_path, updated_groupname_path = update_groupnames()

    print('\nloading divisions\n')
    updated_divisions, previous_divisions, previous_divisions_paths = update_divisions(
        groups_that_changed,updated_groupname_df,previous_groupname_df)

    print('fixing groupnames\n')
    updated_divisions = fix_groupnames(updated_divisions)

    print('\nloading exports\n')
    all_prev_csvs_paths = [previous_groupname_path]+[updated_groupname_path]+previous_divisions_paths
    updated_export,exported_data_path = update_export(updated_divisions,all_prev_csvs_paths)

    print('Exporting everything')
    export_everything(updated_export,updated_divisions,updated_groupname_df,
        previous_groupname_path,previous_divisions_paths,exported_data_path,
        export_path,
        testing = False)

    print('EOF')
