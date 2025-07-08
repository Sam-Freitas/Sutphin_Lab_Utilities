import sys
import os, glob
import pandas as pd
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableView, QPushButton, QVBoxLayout, QWidget, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QDialog, QLabel, 
    QProgressBar, QGridLayout, QCheckBox, QDialogButtonBox
)    
from PyQt6.QtGui import QFont
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtGui import QColor, QBrush

def find_files(folder_path, file_extension='.png', filter='fluorescent_data', filter2 = None):
    """
    Recursively finds and returns all files with the specified extension in the given folder,
    only if the filter string is contained within the file path.

    Args:
        folder_path (str): The path to the folder to search.
        file_extension (str): The file extension to search for (default is '.png').
        filter (str): The filter string that must be in the file path to be included in the result (default is 'fluorescent_data').

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
        return found_files2
    else:
        return found_files

# this deletes all the dir contents, recursive or not 
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

        self.open_button.clicked.connect(self.open_and_transfer_csvs)
        self.save_button.clicked.connect(self.save_csv)
        self.reset_button.clicked.connect(self.reset_changes)

        # Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def open_and_transfer_csvs(self):
        # this function finds and transfers csvs into the temp file location for 
        # faster processing on the local drive
        
        file_path, _ = QFileDialog.getOpenFileName(self, "OPEN THE GROUPNAME.CSV IN GROUPNAMES FOLDER", "", "CSV Files (*Groupname.csv)")

        assert os.path.isfile(file_path)

        root_progressbar, progress_bar, progress_bar_label = create_progress_window()
        update_progress_bar(progress_bar,progress_bar_label,current_iteration=1,total=5,text="Loading Data")

        overarching_Data_path = os.path.split(file_path)[0]
        temp = find_files(overarching_Data_path, file_extension='.csv', filter='', filter2 = None)

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
        file_path = 'temp.csv'

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = CSVEditor()
    editor.resize(1000, 600)
    editor.show()
    app.exec()

    print('finishing export')

    print('exporting groupname to divisions')

    print('exporting divisions to exported csv')
