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

def write_log(txt_input,log_name = "log.txt"):
    print(txt_input)
    with open(os.path.join(log_name), "a") as f:
        f.write(str(txt_input) + '\n')

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

class DataFrameModel(QAbstractTableModel):
    def __init__(self, df, original_df=None):
        super().__init__()
        self._df = df
        self._original_df = original_df if original_df is not None else df.copy()

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            value = self._df.iloc[index.row(), index.column()]
            return str(value)

        # Highlight changed cells
        if role == Qt.BackgroundRole:
            current_value = str(self._df.iloc[index.row(), index.column()])
            original_value = str(self._original_df.iloc[index.row(), index.column()])
            if current_value != original_value:
                return QBrush(QColor("#FFF9C4"))  # light yellow
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            self._df.iloc[index.row(), index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._df.columns[section]
            else:
                return section + 1
        return None

class CSVEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Groupname editor")

        self.df = pd.DataFrame()
        self.original_df = pd.DataFrame()

        self.model = None

        # Table View
        self.view = QTableView()

        # Buttons
        self.open_button = QPushButton("Open and transfer groupname CSVs")
        self.save_button = QPushButton("Save Changes")
        self.reset_button = QPushButton("Reset Changes")
        self.close_button = QPushButton("Finished (Export changes)")

        self.open_button.clicked.connect(self.open_and_transfer_csvs)
        self.save_button.clicked.connect(self.save_csv)
        self.reset_button.clicked.connect(self.reset_changes)
        self.close_button.clicked.connect(self.close_app)

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.close_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def close_app(self):
        QApplication.instance().quit()

    def open_and_transfer_csvs(self):
        # this function finds and transfers csvs into the temp file location for 
        # faster processing on the local drive

        default_file_path = r"C:\Users\LabPC2\Documents\GitHub\Sutphin_Lab_Utilities\_Data_fixes\_Data_copy"
        if not os.path.isdir(default_file_path):
            default_file_path = ''
        
        file_path, _ = QFileDialog.getOpenFileName(self, "OPEN THE GROUPNAME.CSV IN GROUPNAMES FOLDER", default_file_path, "CSV Files (*Groupname.csv)")

        assert os.path.isfile(file_path)

        # progress bar time(!)
        root_progressbar, progress_bar, progress_bar_label = create_progress_window()
        update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=2,text="Loading Data")

        # find the _Data paths or the associated overarching folder
        overarching_Data_path = os.path.split(os.path.split(file_path)[0])[0]
        associated_csvs = find_files(overarching_Data_path, file_extension='.csv', filter='', filter2 = None)

        # create and delete temp files
        os.makedirs('temp_data', exist_ok=True)
        del_dir_contents('temp_data',recursive=True,dont_delete_registrations=False)
        os.makedirs('temp_data', exist_ok=True)

        # transfer data over to the temp folders
        update_progress_bar(progress_bar,progress_bar_label,current_iteration=2,total=2,text="Transfering data")
        with open(os.path.join('temp_data',"path_output.txt"), "w") as f:
            f.write(overarching_Data_path)
        for this_csv in associated_csvs:
            shutil.copy2(this_csv,os.path.join('temp_data',os.path.split(this_csv)[-1]))

        root_progressbar.destroy()

        if file_path:
            self.df = pd.read_csv(file_path, keep_default_na=False, na_values=[])
            self.original_df = self.df.copy()
            self.model = DataFrameModel(self.df, self.original_df)
            self.view.setModel(self.model)
            self.status.showMessage(f"Loaded: {file_path}", 4000)

    def save_csv(self):
        if self.df.empty:
            QMessageBox.warning(self, "No Data", "No CSV file is loaded.")
            return

        # file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV File As", "", "CSV Files (*.csv)")
        file_path = os.path.join('temp_data','Updated_temp_Groupname.csv')

        if file_path:
            self.df.to_csv(file_path, index=False, na_rep='')
            self.status.showMessage(f"Saved: {file_path}", 4000)

    def reset_changes(self):
        if self.df.empty:
            return
        # Reset to original
        self.df = self.original_df.copy()
        self.model = DataFrameModel(self.df, self.original_df)
        self.view.setModel(self.model)
        self.status.showMessage("Table reset to original values.", 4000)

def get_export_path():
    with open(os.path.join('temp_data','path_output.txt'),'r') as f:
        out = f.read()
    return out

def repopulate_NA_dataframe(input_df,use_index_col = False):
    # for each row make sure that something is populated across the NA
    # if anything has been entered

    temp_df = input_df.copy()
    temp_values = input_df.values
    num_rows,num_cols = temp_values.shape

    # this is the defualt
    if not use_index_col:
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
    else:
        num_conditions = int(np.max(np.sum(temp_values != 'NA',axis = 1)))
        pattern1 = ['NA']*(num_cols-1)

        for row_idx in range(num_rows):
            #first check if has correct amount of NAs
            if all(temp_values[row_idx,-1*len(pattern1):] == pattern1):
                # then make sure that something was entered 
                if temp_values[row_idx,1] != 'NA':
                    temp_values[row_idx,2:num_conditions+1] = temp_values[row_idx,1]

        for col_idx,col in enumerate(temp_df.columns):
            temp_df[col].values[:] = temp_values[:,col_idx]
        pass

    return temp_df

def update_groupnames():
    # load in the groupnames

    previous_groupname_path = os.path.join('temp_data','Groupname.csv')
    updated_groupname_path = os.path.join('temp_data','Updated_temp_Groupname.csv')

    previous_groupname_df = pd.read_csv(previous_groupname_path, keep_default_na=False, na_values=[])
    updated_groupname_df = pd.read_csv(updated_groupname_path, keep_default_na=False, na_values=[])

    # populating the array with the non-changed variables
    # if the first two items are the descriptor (eg egg date) and a value (eg 2025-1-1)
    # and the rest are NA
    # then populate across the rest of the data that value
    previous_groupname_df = repopulate_NA_dataframe(previous_groupname_df)
    updated_groupname_df = repopulate_NA_dataframe(updated_groupname_df)

    # finding which groups have been changed
    # the False values are the changed arrays
    changed_array = (previous_groupname_df == updated_groupname_df)
    changed_array_values = changed_array.values
    # list(changed_array.columns)[1:]

    groups_that_changed = []
    for this_column in list(changed_array.columns):
        if 'group' in this_column:
            if False in changed_array[this_column].values:
                print(this_column, '--- changed')
                # print(changed_array[this_column].values)
                groups_that_changed.append(this_column)
            # else:
            #     print(this_column, '--- NOT changed')
            # print(changed_array[this_column])

    return groups_that_changed, updated_groupname_df, previous_groupname_df,previous_groupname_path ,updated_groupname_path

def update_divisions(groups_that_changed,updated_groupname_df,previous_groupname_df, divisions_paths = None):

    if divisions_paths is None:
        divisions_paths = natsorted(find_files('temp_data',file_extension='.csv',filter='_divisions.csv'))
    else:
        pass

    condition_parts = updated_groupname_df['VariableName'].values

    old_groupnames_need_updating = previous_groupname_df[groups_that_changed]
    new_groupnames_for_updating = updated_groupname_df[groups_that_changed]

    divisions_df_list = []
    for i,each_division_path in enumerate(divisions_paths):
        temp_df = pd.read_csv(each_division_path, keep_default_na=False, na_values=[])
        divisions_df_list.append(temp_df)
    del each_division_path

    previous_divisions = copy.deepcopy(divisions_df_list)

    # find the unique divisions for the old ones
    # match it up to the new updated divisions 
    # update the divisions that are associated 

    for i,each_division in enumerate(divisions_df_list):
        # find the unique divisions for the old not updated divisions 
        each_division = each_division.astype(object)
        each_divison_values = np.asarray(each_division[condition_parts])
        # each_unique_divisions = np.unique(each_divison_values,axis = 0)

        # for each group iterate through all the divisions that need to be changed and then 
        # overwrite them(?)
        for j, this_group in enumerate(groups_that_changed):
            this_condition_to_change = np.asarray(old_groupnames_need_updating[this_group])

            for k,this_worms_condition in enumerate(each_divison_values):
                if (this_condition_to_change.astype(str) == this_worms_condition.astype(str)).all():
                    # changing everything to object works
                    # check final output
                    each_division.loc[k,condition_parts] = np.asarray(new_groupnames_for_updating[this_group]).astype(object)
        divisions_df_list[i] = each_division

    return divisions_df_list, previous_divisions, divisions_paths

def fix_groupnames(updated_divisions,
    use_logging = False, log_name = "log.txt"):
    # this finds and updates the groupnames from the divisions
    combined_updated_divisions = pd.concat(updated_divisions)
    # get the unique groupnames that are not worm number or date (first 3 conditions)
    temp_array = np.asarray(combined_updated_divisions)[:,3:-1]
    unique_groups_full = np.unique(temp_array.astype(str),axis = 0)

    # this checks to see which conditions are actually changed
    short_groupname_bool_vector = []
    for i,temp_var in enumerate(unique_groups_full[0]):
        temp_vector = unique_groups_full[:,i]
        all_conditions_same_bool = all(temp_vector == temp_var)
        short_groupname_bool_vector.append(all_conditions_same_bool)
    short_groupname_bool_vector_inv = [not elem for elem in short_groupname_bool_vector]

    # find which groups of conditions are actually unique
    vectored_unique_groups = unique_groups_full[:,short_groupname_bool_vector_inv]
    changed_groups = np.unique(vectored_unique_groups)

    # get the vector that represents which conditions got changed for a groupname
    full_groupname_bool_vector_inv = [False,False,False]+short_groupname_bool_vector_inv+[False]

    running_groupnames = []

    # this has been tested with only a single groupame change
    for div_idx,this_division in enumerate(updated_divisions):

        # this finds the column that is changed with the groupname
        change_lookup = np.asarray(this_division[this_division.columns[full_groupname_bool_vector_inv]])

        # for all of the possible groupnames find the matching one
        new_groupname_for_this_divison = []
        for temp in change_lookup:
            # find which groupname is this one using matching of the vector
            vector_idx_groupname = (np.sum(vectored_unique_groups == temp,axis = 1) == len(temp))
            temp_groupname = vectored_unique_groups[vector_idx_groupname]
            new_groupname_for_this_divison.append(temp_groupname)

        # convert to an array
        new_groupname_for_this_divison = np.asarray(new_groupname_for_this_divison).astype(object).squeeze()

        # check to make sure that the groups are combined into a single column
        if len(new_groupname_for_this_divison.shape) > 1:
            temp = new_groupname_for_this_divison.copy()
            temp[:,0:-1] = temp[:,0:-1] +','
            temp = np.sum(temp,axis = 1).squeeze()
            new_groupname_for_this_divison = temp

        running_groupnames.append(new_groupname_for_this_divison)

        this_division['Groupname'] = new_groupname_for_this_divison
        updated_divisions[div_idx] = this_division

    if not use_logging:
        print('New Groupnames:')
    else:
        write_log('New Groupnames:',log_name=log_name)
    for each_new_groupname in np.unique(running_groupnames):
        if not use_logging:
            print('---',each_new_groupname)
        else:
            write_log('--- ' + each_new_groupname,log_name=log_name)

    return updated_divisions

def update_export(updated_divisions,all_prev_csvs_paths,exported_data_path = None):

    # update the groupnames in the exported data files
    # use the temp files if no export file is given

    combined_updated_divisions = pd.concat(updated_divisions)

    if exported_data_path is None:
        all_csvs = natsorted(find_files('temp_data',file_extension='.csv',filter=''))

        for this_csv in all_csvs:
            if this_csv not in all_prev_csvs_paths:
                exported_data_path = this_csv 
    else:
        pass

    exported_data = pd.read_csv(exported_data_path, keep_default_na=False, na_values=[])

    try:
        exported_data['Groupname'] = np.asarray(combined_updated_divisions['Groupname'])
    except:
        print('!!!!!! Assignment of the updated GROUPNAME failed')
        
        # this is most likely from omission of a plate (skipped one)
        # this attempts to find which divisions (plates) are used in the experiment

        divisions_paths = natsorted(find_files(os.path.split(exported_data_path)[0],file_extension='_divisions.csv'))
        divisions_paths_names = [os.path.split(a)[-1].replace('_divisions.csv','') for a in divisions_paths]

        list_of_div_to_use = []
        for i,(temp_div_path_name,this_division) in enumerate(zip(divisions_paths_names,updated_divisions)):
            if temp_div_path_name in np.unique(exported_data['Plate ID']):
                print(temp_div_path_name)
                list_of_div_to_use.append(this_division)

        combined_updated_divisions = pd.concat(list_of_div_to_use)

        exported_data['Groupname'] = np.asarray(combined_updated_divisions['Groupname'])

        pass

    return exported_data, exported_data_path

def export_everything(updated_export,updated_divisions,updated_groupname_df,
        previous_groupname_path,previous_divisions_paths,exported_data_path,
        export_path,
        testing = True, temp_export = True, use_logging = False,log_name = "log.txt"):

    temp_export_path = os.path.join('temp_data','exported_data')
    os.makedirs(temp_export_path,exist_ok=True)
    del_dir_contents(temp_export_path,recursive=True,dont_delete_registrations=False)
    os.makedirs(temp_export_path,exist_ok=True)

    # this exports back into the 
    if temp_export:
        if not use_logging:
            print('Temporary export:')
        else:
            write_log('Temporary export:',log_name=log_name)

        # groupname temp export
        temp_groupname_export_path = os.path.join(temp_export_path,os.path.split(previous_groupname_path)[-1])
        if not use_logging:
            print('---', temp_groupname_export_path)
        else:
            write_log('--- ' + temp_groupname_export_path,log_name=log_name)
        updated_groupname_df.to_csv(temp_groupname_export_path,index = False)

        # divisions temp export
        for div_idx, (this_division,this_previous_division_path) in enumerate(zip(updated_divisions,previous_divisions_paths)):
            this_temp_division_export_path = os.path.join(temp_export_path,os.path.split(this_previous_division_path)[-1])
            if not use_logging:
                print('---',div_idx+1,this_temp_division_export_path)
            else:
                write_log('--- ' + str(div_idx+1) + ' ' + this_temp_division_export_path, log_name = log_name)
            this_division.to_csv(this_temp_division_export_path,index = False)

        # data export
        temp_exported_data_export_path = os.path.join(temp_export_path,os.path.split(exported_data_path)[-1])
        if not use_logging:
            print('---', temp_exported_data_export_path)
        else:
            write_log('--- ' + temp_exported_data_export_path, log_name = log_name)
        updated_export.to_csv(temp_exported_data_export_path,index = False)
    
    if not use_logging:
        print('Re-Exporing back into the data path')
    else:
        write_log('Re-Exporing back into the data path', log_name = log_name)

    # from old code
    data_output_path = export_path

    # groupname final export
    final_groupname_export_path = os.path.join(data_output_path,'Groupnames',os.path.split(previous_groupname_path)[-1])
    if not use_logging:            
        print('---', final_groupname_export_path)
    else:
        write_log('--- ' + final_groupname_export_path, log_name = log_name)
    if not testing:
        updated_groupname_df.to_csv(final_groupname_export_path,index = False)

    # divisions final export
    for div_idx, (this_division,this_previous_division_path) in enumerate(zip(updated_divisions,previous_divisions_paths)):
        this_final_division_export_path = os.path.join(data_output_path,'divisions',os.path.split(this_previous_division_path)[-1])
        if not use_logging:
            print('---',div_idx+1,this_final_division_export_path)
        else:
            write_log('--- ' + str(div_idx+1) + ' ' + this_final_division_export_path, log_name = log_name)
        if not testing:
            this_division.to_csv(this_final_division_export_path,index = False)

    # data export
    final_exported_data_export_path = os.path.join(data_output_path,os.path.split(exported_data_path)[-1])
    if not use_logging:
        print('---', final_exported_data_export_path)
    else:
        write_log('--- ' + final_exported_data_export_path, log_name = log_name)
    if not testing:
        updated_export.to_csv(final_exported_data_export_path,index = False)

    return 1
