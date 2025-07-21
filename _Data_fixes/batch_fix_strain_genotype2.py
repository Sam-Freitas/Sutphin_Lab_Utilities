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

def write_log(txt_input):
    print(txt_input)
    with open(os.path.join("log.txt"), "a") as f:
        f.write(txt_input + '\n')

def get_experiment_name(this_path):
    path = os.path.normpath(this_path)
    return path.split(os.sep)[-3]

def get_path_parts(this_path):
    path = os.path.normpath(this_path)
    return path.split(os.sep)

def find_files(folder_path, file_extension='.png', filter='', filter2 = None, exclude_filter = None):
    """
    Recursively finds and returns all files with the specified extension in the given folder,
    only if the filter string is contained within the file path.

    Args:
        folder_path (str): The path to the folder to search.
        file_extension (str): The file extension to search for (default is '.png').
        filter (str): The filter string that must be in the file path to be included in the result (default is '').

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
        found_files =  found_files2
    
    if exclude_filter:
        non_excluded_files = []
        for file in found_files:
            if exclude_filter not in file:
                non_excluded_files.append(file)
        found_files = non_excluded_files

    return found_files

def del_dir_contents(path_to_dir, recursive = False, dont_delete_registrations = True): 
    if recursive:
        files = glob.glob(os.path.join(path_to_dir,'**/*'), recursive=recursive)
        for f in files:
            if not os.path.isdir(f):
                if dont_delete_registrations:
                    if 'registrations' not in f:
                        os.remove(f)
                else:
                    os.remove(f)
    else: # default
        files = glob.glob(os.path.join(path_to_dir,'*'))
        for f in files:
            if dont_delete_registrations:
                os.remove(f)
            else:
                os.remove(f)

def create_progress_window():
    # Create dialog window
    root_progressbar = QDialog()
    root_progressbar.setWindowTitle("Progress Bar")
    root_progressbar.setWindowFlags(root_progressbar.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

    # Create vertical layout
    layout = QVBoxLayout()

    # Create progress bar
    progress_bar = QProgressBar()
    progress_bar.setOrientation(Qt.Orientation.Horizontal)
    progress_bar.setMaximum(100)
    progress_bar.setMinimum(0)
    layout.addWidget(progress_bar)

    # Create label for displaying text over the progress bar
    progress_bar_label = QLabel("")
    progress_bar_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    layout.addWidget(progress_bar_label)

    root_progressbar.setLayout(layout)
    root_progressbar.show()

    return root_progressbar, progress_bar, progress_bar_label

def update_progress_bar(progress_bar, label, current_iteration, total, text=""):
    progress_percentage = (current_iteration / total) * 100
    progress_bar.setValue(int(progress_percentage))

    # Update label text
    text = text[:100]  # Limit text length to 100 characters
    text = text.ljust(50)  # Pad text with spaces to ensure consistent display width
    label.setText(text)

    QApplication.processEvents()  # Update the progress bar

def repopulate_NA_dataframe(input_df):
    # for each row make sure that something is populated across the NA
    # if anything has been entered

    temp_df = input_df.copy()
    temp_values = input_df.values
    num_rows,num_cols = temp_values.shape

    # this finds all the NOT NA values and finds the column with the most (minus the row header)
    num_conditions = int(np.max(np.sum(temp_values != 'NA',axis = 1))) - 1

    pattern1 = ['NA']*(num_cols-2)

    for row_idx in range(num_rows):
        #first check if has correct amount of NAs
        if all(temp_values[row_idx,-1*len(pattern1):] == pattern1):
            # then make sure that something was entered 
            if temp_values[row_idx,1] != 'NA':
                temp_values[row_idx,2:num_conditions+1] = temp_values[row_idx,1]

    for col_idx,col in enumerate(temp_df.columns):
        temp_df[col].values[:] = temp_values[:,col_idx]

    return temp_df

if __name__ == "__main__":

    try:
        os.remove('log.txt')
        write_log("restarted LOGGING")
    except:
        write_log("New LOGGING")

    app = QApplication(sys.argv)

    # load in the data copy from the local drive
    overarching_Data_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_copy"
    assert(os.path.isdir(overarching_Data_path))
    write_log("found _Data path:",)
    write_log(overarching_Data_path)

    # output path
    output_path = overarching_Data_path

    # load in the frozen stock keys that we use 
    frozen_stock_KEY = pd.read_csv(r'_Data_fixes\Sutphin Worm Frozen Stock AZ.csv', keep_default_na=False, na_values=[])
    strain_genotype_lookup = frozen_stock_KEY[['GLS Strain','Strain','Genotype']]

    # make a copy of the strains as a lower() for ease of matching
    strain_genotype_lookup_lower = strain_genotype_lookup.copy().map(str.lower)

    # progress bar time(!)
    root_progressbar, progress_bar, progress_bar_label = create_progress_window()
    update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_groupname_csvs = natsorted(find_files(overarching_Data_path, file_extension='.csv', filter='Groupname.csv', filter2 = None))
    write_log('')

    for i,this_found_groupname_csv in enumerate(found_groupname_csvs):

        continue_flag = False
        try:

            # get the name and update the 
            this_exp_name = get_experiment_name(this_found_groupname_csv)
            write_log(this_exp_name)
            progress_bar_text = this_exp_name+'-'*(50-len(this_exp_name))+str(i+1)+'/'+str(len(found_groupname_csvs))
            update_progress_bar(progress_bar,progress_bar_label,current_iteration=i+1,total=len(found_groupname_csvs),
                text=progress_bar_text)
            
            # Groupname find
            this_groupname = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='Groupname.csv')[0]

            # divisions find
            this_divisions = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='_divisions.csv')

            # exported dats find
            this_exported_data = find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='')
            for temp in [this_groupname] + this_divisions:
                this_exported_data.remove(temp)
            this_exported_data = this_exported_data[0]
            continue_flag = True
        except:
            write_log(this_exp_name + ' ----- FAILED TO LOAD ALL DATA')
            continue_flag = False

        if continue_flag:
            # isolate each groups strain and genotype data
            this_groupname_df = pd.read_csv(this_groupname, keep_default_na=False, na_values=[])
            this_groupname_df = repopulate_NA_dataframe(this_groupname_df)

            strain_df = this_groupname_df.loc[this_groupname_df['VariableName'] == 'Strain Names',:].iloc[:,1:]
            genotype_df = this_groupname_df.loc[this_groupname_df['VariableName'] == 'Genotypes',:].iloc[:,1:]
            strain_df_array = np.asarray(strain_df).squeeze()
            genotype_df_array = np.asarray(genotype_df).squeeze()

            # use the lookup table to make sure that everything is looking good
            for j,(this_groups_strain,this_groups_genotype) in enumerate(zip(strain_df_array,genotype_df_array)):
                if (this_groups_strain != 'NA') and (this_groups_genotype != 'NA'):
                    # force them to be lower for matching
                    temp_this_groups_strain = this_groups_strain.lower()
                    temp_this_groups_genotype = this_groups_genotype.lower()

                    # remove any space from the strain name 
                    temp_this_groups_strain = temp_this_groups_strain.replace(' ','')

                    # find all the possible matches for the strain (assumed correct)
                    # only use the lower() array for matching 
                    possible_matches = strain_genotype_lookup.iloc[np.where(strain_genotype_lookup_lower['Strain']==temp_this_groups_strain)[0],:]

                    if not possible_matches.empty:
                        # matched pair [GLS strain, Strain, Genotype]
                        if possible_matches.shape[0] > 1:
                            matched_pair = possible_matches.iloc[0,:]
                        else:
                            matched_pair = possible_matches
                        matched_pair = np.asarray(matched_pair).squeeze()

                        # write_log(this_groups_strain + '---' + this_groups_genotype)
                        # write_log(matched_pair[1] + '+++' + matched_pair[2])

                        if this_groups_genotype.lower() != matched_pair[2].lower():
                            write_log('============> ' + this_groups_strain + '(' + this_groups_genotype + ')' + ' #### TO #### ' + matched_pair[1] + '(' + matched_pair[2] + ')' )

                        # NOW UPDATE THE GROUPNAME AND DIVISIONS AND EXPORTED DATA
                        # yay
                    else:
                        write_log('!!!!SKIPPED -  ' + this_groups_strain + '(' + this_groups_genotype + ')')


        # print('FIX THE groupname strain->genotype')
        # print('Fix the associated divisions')
        # print('fix the exports ')
        write_log('')

        # except:
        #     write_log('--------- FAILED')



    write_log('asdfasdf')