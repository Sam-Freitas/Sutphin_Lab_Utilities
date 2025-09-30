import os, sys
import glob
from natsort import natsorted

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

if __name__ == "__main__":

    print("EOF")
