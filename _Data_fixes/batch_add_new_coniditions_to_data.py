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

## this code finds and updates all the conditions to add the newer conditions 
## that are outlined in the Groupname_template_added_conditions_blank csv

if __name__ == "__main__":
    
    file_name = os.path.splitext(os.path.basename(__file__))[0]
    log_path = 'log_' + file_name + '.txt'


    ########################################## THIS IS MANUAL AND MUST BE SET BY THE USER
    ######################################### 
    custom_col_locations = {'Well Location':0,'Groupname':-1}
    ########################################## this determines the order of speicific parts of the 
    #########################################  _divisions.csv that are not inherently present in the groupname.csv 

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

    groupname_template_updated_blank_df = pd.read_csv(
        r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\Groupname_template_added_conditions_blank.csv",
        keep_default_na=False, na_values=[],index_col = 'VariableName')

    # make a copy of the strains as a lower() for ease of matching
    strain_genotype_lookup_lower = frozen_stock_KEY.copy().map(str).map(str.lower)

    # get the new index (conditions names)
    new_conditions_names = list(groupname_template_updated_blank_df.index)



    # progress bar time(!)
    root_progressbar, progress_bar, progress_bar_label = create_progress_window()
    update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_groupname_csvs = natsorted(find_files(overarching_Data_path, file_extension='.csv', filter='Groupname.csv', filter2 = None))
    write_log('',log_name=log_path)

    list_of_all_cols = []

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
            this_divisions = natsorted(find_files(os.path.join(overarching_Data_path,this_exp_name), file_extension='.csv',filter='_divisions.csv'))

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
            this_groupname_df = pd.read_csv(this_groupname, keep_default_na=False, na_values=[], index_col='VariableName')

            updated_groupname_df = groupname_template_updated_blank_df.copy()
            previous_groupname_df = this_groupname_df.copy()

            updated_col_names = updated_groupname_df.columns
            prev_col_names = previous_groupname_df.columns

            # update and expand the groupname df
            for j, this_group in enumerate(updated_col_names):
                # print(j,this_group)
                if this_group in (prev_col_names):
                    temp = this_groupname_df[this_group]
                    updated_groupname_df[this_group] = temp
                else:
                    updated_groupname_df[this_group] = 'NA'
            # fill in the missing values
            updated_groupname_df = updated_groupname_df.fillna('NA')

            # make sure that the dataframe has no NAs where unnecessary
            updated_groupname_df = repopulate_NA_dataframe(updated_groupname_df, use_index_col=True)

            # now update the divisions
            # no need to update the exported data as that only is touched by the groupname variable

            # load in all the divisions
            updated_divisions = []
            for this_divisions_path in this_divisions:
                temp = pd.read_csv(this_divisions_path, keep_default_na=False, na_values=[])
                updated_divisions.append(temp)

            # find the order in which the output will be put in
            order_of_col_names = new_conditions_names.copy()
            for this_custom_col_locations in custom_col_locations:
                if custom_col_locations[this_custom_col_locations] < 0:
                    temp_idx = custom_col_locations[this_custom_col_locations] + len(order_of_col_names) + 1
                    order_of_col_names.insert(temp_idx,this_custom_col_locations)
                else:
                    order_of_col_names.insert(custom_col_locations[this_custom_col_locations],this_custom_col_locations)

            write_log(order_of_col_names,log_name=log_path)

            # expand the divisions
            for division_idx, this_division in enumerate(updated_divisions):
                # isolate single divisioins
                prev_col_names = list(this_division.columns)
                for j, this_condition_col_name in enumerate(new_conditions_names):
                    # either populate where the division already was
                    if this_condition_col_name in (prev_col_names):
                        temp = this_division[this_condition_col_name]
                        this_division[this_condition_col_name] = temp
                    # or add a new column and give it all 'NA'
                    else:
                        this_division[this_condition_col_name] = 'NA'
                this_division = this_division[order_of_col_names]
                this_division.fillna('NA')
                updated_divisions[division_idx] = this_division

            pass

            # EXPORT THEM BACK INTO WHERE THEY WERE FOUND
            # export the groupname.csv

            updated_groupname_df.to_csv(this_groupname,index = True)
            write_log(this_groupname,log_name=log_path)

            for this_division,this_division_path in zip(updated_divisions,this_divisions):
                this_division.to_csv(this_division_path,index = False)
                write_log(this_division_path,log_name=log_path)


        write_log('',log_name=log_path)

        # except:
        #     write_log('--------- FAILED')

    # combined_duplicated_df = pd.concat(duplicates_df)
    # combined_duplicated_df.to_csv('_Data_fixes/dupliucated_strains.csv',index = False)
    write_log('FINSIHED with no errors',log_name=log_path)