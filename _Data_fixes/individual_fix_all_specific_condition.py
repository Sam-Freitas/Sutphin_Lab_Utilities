import sys
import os, glob, shutil, copy, time
import webbrowser
from natsort import natsorted
import numpy as np
import Levenshtein
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

## this code is for a person to go through each experiment that is specified (eg RNAi)
## and change the Groupname.csv using the interactive editor
## a helper function also tries to find the closest robot sheet name and opens that along side (beta)

if __name__ == "__main__":
    
    file_name = os.path.splitext(os.path.basename(__file__))[0]
    log_path = 'log_' + file_name + '.txt'

    use_progressbar = False

    try:
        os.remove(log_path)
        write_log("restarted LOGGING",log_name=log_path)
    except:
        write_log("New LOGGING",log_name=log_path)

    app = QApplication(sys.argv)

    # load in the data copy from the local drive
    overarching_Data_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_copy"
    robot_experiment_sheets_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\robot_sheets"
    assert(os.path.isdir(overarching_Data_path))
    assert(os.path.isdir(robot_experiment_sheets_path))
    write_log("found _Data path:",log_name=log_path)
    write_log(overarching_Data_path,log_name=log_path)
    write_log("found Robot sheets path:",log_name=log_path)
    write_log(robot_experiment_sheets_path,log_name=log_path)
    
    # output path
    output_path = overarching_Data_path

    # progress bar time(!)
    if use_progressbar:
        root_progressbar, progress_bar, progress_bar_label = create_progress_window()
        update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Finding data")

    found_groupname_csvs = natsorted(find_files(overarching_Data_path, file_extension='.csv', filter='Groupname.csv', filter2 = None))
    found_robot_sheets_pdf = natsorted(find_files(robot_experiment_sheets_path, file_extension='.pdf', filter='', filter2 = None))

    robot_sheets_names = [os.path.splitext(os.path.split(temp)[-1])[0] for temp in found_robot_sheets_pdf]

    write_log('',log_name=log_path)

    perfect_matches = 0
    imperfect_matches = 0

    start_at = 100

    for i,this_found_groupname_csv in enumerate(found_groupname_csvs):

        continue_flag = False
        try:

            # get the name of the experiment
            this_exp_name = get_experiment_name(this_found_groupname_csv)
            write_log(this_exp_name,log_name=log_path)
            if use_progressbar:
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

        if (i >= start_at) and (continue_flag == True):
            continue_flag = True
        else:
            continue_flag = False

        if continue_flag:
            imperfect_match_flag = False
            perfect_match_flag = False
            # isolate each groups strain and genotype data
            this_groupname_df = pd.read_csv(this_groupname, keep_default_na=False, na_values=[], index_col='VariableName')

            # calculate the levenshtein distance 
            # it gets the closest names to the experiment names
            lev_distances = []
            for this_robot_sheet_name in robot_sheets_names:
                dist_calc = Levenshtein.distance(this_exp_name.lower(),this_robot_sheet_name.lower())
                lev_distances.append(dist_calc)
            lev_distances = np.asarray(lev_distances)
            found_minimum_idx = np.where(lev_distances == lev_distances.min())[0]

            # if there are multiple minimuns we have problem
            if len(found_minimum_idx) > 1:
                possible_matches = np.asarray(robot_sheets_names)[found_minimum_idx]
                secondary_distances = []
                for this_match in possible_matches:
                    dist_calc = Levenshtein.jaro_winkler(this_exp_name.lower(),this_match.lower())
                    secondary_distances.append(dist_calc)
                found_minimum_idx = found_minimum_idx[np.argmin(secondary_distances)]
            # otherwise just use that first one
            else:
                found_minimum_idx = int(found_minimum_idx.squeeze())

            # if something goes wrong then report it

            if lev_distances[found_minimum_idx] > 0:
                write_log('############################################CHECKOUT', log_name=log_path)
                imperfect_matches += 1
                imperfect_match_flag = True
            else:
                perfect_matches += 1
                perfect_match_flag = True

            # log that b
            write_log('--- Sheet:   ' + robot_sheets_names[int(found_minimum_idx)] , log_name=log_path)
            write_log('--- Levdst:  ' + str(lev_distances[found_minimum_idx]), log_name=log_path)

            if lev_distances[found_minimum_idx] > 0:
                pass
                # this is probably a good alert for when the sheet doesnt match perfectly

            write_log(found_robot_sheets_pdf[found_minimum_idx],log_name=log_path)
            write_log(this_groupname, log_name=log_path)
            write_log(str(i) + ' --- sheet NUMBER',log_name=log_path)

            webbrowser.open(found_robot_sheets_pdf[found_minimum_idx])

            # THIS IS THE MANUAL OPENING FOR THE GROUPNAME EDITOR
            editor = CSVEditor(options=this_groupname)
            editor.resize(1000, 600)
            editor.show()
            app.exec()

            write_log('finishing and exporting changes---------------',log_name=log_path)   
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
            if (updated_export is not None) and (exported_data_path is not None):
                export_everything(updated_export,updated_divisions,updated_groupname_df,
                    previous_groupname_path,previous_divisions_paths,exported_data_path,
                    export_path,
                    testing = False)
            else:
                write_log('ERROR',log_name=log_path)
                write_log('SKIPPING',log_name=log_path)

            pass
            
            ########################### here we do the stuff
            ########################### automatically open the csv editor and other stuff
            ########################### probably have a way to only check for specific things 
            ########################### like compounds or RNAi or other (????) 

        write_log('',log_name=log_path)

    write_log('Perfect matches: ' + str(perfect_matches) + '/' + str(perfect_matches+imperfect_matches),log_name=log_path)
    write_log('Imperfect matches: ' + str(imperfect_matches) + '/' + str(perfect_matches+imperfect_matches),log_name=log_path)
    write_log('FINSIHED with no errors',log_name=log_path)