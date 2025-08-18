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
    
    file_name = os.path.splitext(os.path.basename(__file__))[0]
    log_path = 'log_' + file_name + '.txt'

    duplicates_name = []
    duplicates_df = []

    try:
        os.remove(log_path)
        write_log("restarted LOGGING",log_name=log_path)
    except:
        write_log("New LOGGING",log_name=log_path)

    app = QApplication(sys.argv)

    # load in the data copy from the local drive
    overarching_Data_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_to_update"
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

    list_of_all_RNAi = []

    for i,this_found_groupname_csv in enumerate(found_groupname_csvs):

        continue_flag = False
        try:

            # get the name and update the 
            this_exp_name = get_experiment_name(this_found_groupname_csv)
            write_log(this_exp_name,log_name=log_path)
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
            write_log(this_exp_name + ' ----- FAILED TO LOAD ALL DATA',log_name=log_path)
            continue_flag = False

        if continue_flag:
            # isolate each groups strain and genotype data
            this_groupname_df = pd.read_csv(this_groupname, keep_default_na=False, na_values=[])
            this_groupname_df = repopulate_NA_dataframe(this_groupname_df)

            previous_groupname_df = this_groupname_df.copy()
            updated_groupname_df = this_groupname_df.copy()

            RNAi_df = this_groupname_df.loc[this_groupname_df['VariableName'] == 'RNAi [gene-1(RNAi)]',:].iloc[:,1:]
            RNAi_df_array = np.asarray(RNAi_df).squeeze()
            groups_col_name_df_array = np.asarray(list(this_groupname_df.columns)[1:]).squeeze()

            groups_that_changed = []
            export_this_data_if_changed = True
            # use the lookup table to make sure that everything is looking good
            # if they dont match then replace it with the look up table 

            for j,(this_groups_RNAi,this_groups_col_name) in enumerate(zip(RNAi_df_array,groups_col_name_df_array)):
                if (this_groups_RNAi != 'NA'):
                    # force them to be lower for matching
                    temp_this_groups_RNAi = this_groups_RNAi.lower()

                    # remove any space from the strain name 
                    temp_this_groups_RNAi = temp_this_groups_RNAi.replace(' ','')

                    list_of_all_RNAi.append(temp_this_groups_RNAi)

                    # find all the possible matches for the strain (assumed correct)
                    # only use the lower() array for matching 
                    possible_matches = (temp_this_groups_RNAi == 'ev')

                    # make sure that there is a match to the ev lookup table
                    if possible_matches:

                        # update the groupname DF with the new genotype values
                        write_log('============> ' + temp_this_groups_RNAi + ' #### TO #### ' + 'EV(RNAi)' ,
                            log_name=log_path)

                        # update the ev -> EV(RNAi)
                        row_indexer_strain = (updated_groupname_df['VariableName'] == 'RNAi [gene-1(RNAi)]').values
                        updated_groupname_df.loc[row_indexer_strain,str(this_groups_col_name)] = 'EV(RNAi)'
                        
                        # record that the group changed
                        groups_that_changed.append(str(this_groups_col_name))
                        pass

                        # NOW UPDATE THE GROUPNAME AND DIVISIONS AND EXPORTED DATA
                        # yay
            pass

            # if something changed then re-export all the data 
            if groups_that_changed:
                # make sure that nothing was skipped
                if export_this_data_if_changed:

                    export_path = os.path.join(overarching_Data_path,this_exp_name)
                    previous_groupname_path = this_groupname
                    updated_groupname_path = this_groupname
                    # updated_groupname_df, previous_groupname_df

                    # print('\nloading divisions\n')
                    updated_divisions, previous_divisions, previous_divisions_paths = update_divisions(
                        groups_that_changed,updated_groupname_df,previous_groupname_df, divisions_paths=this_divisions)

                    # update the groupnames on the divisions
                    updated_divisions = fix_groupnames(updated_divisions,use_logging=True,log_name=log_path)

                    # update the groupnames on the exported data file
                    updated_export,exported_data_path = update_export(updated_divisions,'',exported_data_path=this_exported_data)

                    export_everything(updated_export,updated_divisions,updated_groupname_df,
                        previous_groupname_path,previous_divisions_paths,exported_data_path,
                        export_path,
                        testing = False, 
                        temp_export=False, use_logging=True,log_name=log_path)
                    pass
                pass

        write_log('',log_name=log_path)

        # except:
        #     write_log('--------- FAILED')

    # combined_duplicated_df = pd.concat(duplicates_df)
    # combined_duplicated_df.to_csv('_Data_fixes/dupliucated_strains.csv',index = False)
    write_log('FINSIHED with no errors',log_name=log_path)