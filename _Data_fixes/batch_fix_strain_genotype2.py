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
    
    log_path = 'log_batch_fix_genotype.txt'

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

                        # for output only
                        # check if already done
                        if temp_this_groups_strain not in duplicates_name:
                            # if possible_matches.shape[0] > 1:
                            duplicates_name.append(temp_this_groups_strain)
                            duplicates_df.append(possible_matches)
                            temp = pd.DataFrame(columns = possible_matches.columns)
                            temp.loc[0] = ''
                            duplicates_df.append(temp)

                        # matched pair [GLS strain, Strain, Genotype]
                        if possible_matches.shape[0] > 1:
                            matched_pair = possible_matches.iloc[0,:]
                        else:
                            matched_pair = possible_matches.iloc[0,:]
                        # matched_pair = np.asarray(matched_pair).squeeze()

                        # write_log(this_groups_strain + '---' + this_groups_genotype)
                        # write_log(matched_pair[1] + '+++' + matched_pair[2])

                        if this_groups_genotype.lower() != matched_pair['Genotype'].lower():
                            write_log('============> ' + this_groups_strain + '(' + this_groups_genotype + ')' + ' #### TO #### ' + matched_pair['Strain'] + '(' + matched_pair['Genotype'] + ')' ,
                            log_name=log_path)

                        # NOW UPDATE THE GROUPNAME AND DIVISIONS AND EXPORTED DATA
                        # yay
                    else:
                        write_log('!!!!SKIPPED -  ' + this_groups_strain + '(' + this_groups_genotype + ')',log_name=log_path)


        # print('FIX THE groupname strain->genotype')
        # print('Fix the associated divisions')
        # print('fix the exports ')
        write_log('',log_name=log_path)

        # except:
        #     write_log('--------- FAILED')


    combined_duplicated_df = pd.concat(duplicates_df)
    combined_duplicated_df.to_csv('_Data_fixes/dupliucated_strains.csv',index = False)
    write_log('asdfasdf',log_name=log_path)