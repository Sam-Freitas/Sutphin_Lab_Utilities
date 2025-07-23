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
    
    log_path = 'log_find_strain_duplicates.txt'

    try:
        os.remove(log_path)
        write_log("restarted LOGGING",log_name=log_path)
    except:
        write_log("New LOGGING",log_name=log_path)

    app = QApplication(sys.argv)

    # load in the frozen stock keys that we use 
    frozen_stock_KEY = pd.read_excel(r'_Data_fixes\Sutphin Worm Frozen Stock AZ.xlsx',sheet_name=1,keep_default_na=False,na_values=[])
    strain_genotype_lookup = frozen_stock_KEY[['GLS Strain','Strain','Genotype']]

    # make a copy of the strains as a lower() for ease of matching
    strain_genotype_lookup_lower = strain_genotype_lookup.copy().map(str.lower)

    blanks = np.asarray(strain_genotype_lookup_lower['Strain'])==''
    not_blanks = [not elem for elem in blanks]

    df_lower = frozen_stock_KEY.loc[not_blanks]
    df_lower.to_excel('_Data_fixes/cleaned_frozen_stock.xlsx',index=False)

    print('asdf')