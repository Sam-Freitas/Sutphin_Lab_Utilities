import os,sys,glob,re,shutil
import pandas as pd
import numpy as np
from natsort import natsorted

# this script will copy the setup from one experiment to another
# this assumes that at least the first 'experiment_to_copy' has the divisions and groupnams set up and run

# make sure that these are changed before running
experiment_path_to_copy = '/xdisk/sutphin/samfreitas/Cholesterol_screen_013'
experiment_path_to_receive = '/xdisk/sutphin/samfreitas/Cholesterol_screen_014'

# the first one is to be found the second one is the replacement
# make sure that the dates are not overlapping and messing each other up
paired_replacements = [['2025-08-07','2025-08-13'],
                        ['2025-08-09','2025-08-15'],
                        ['mvb-12(RNAi)','rab-7(RNAi)'],
                        ['F25H2.6(RNAi)','spe-4(RNAi)'],
                        ['pmp-4(RNAi)','miga-1(RNAi)'],
                        ]

print('Are the settings correct?\n\n')

# make sure that these are changed before running
print('experiment_path_to_copy = ' + experiment_path_to_copy)
print('experiment_path_to_receive = ' + experiment_path_to_receive)

print('paired_replacements = ' + str(paired_replacements))

print('\n\n')
user_continue = input('---[yes(y)/no(n)]')

if user_continue.lower() != 'y' and user_continue.lower() != 'yes':
    print('Ending the program')
    sys.exit()
else:
    print('Continuing')

# do not change this path
path_to_Data = '/groups/sutphin/_Data/'

# this is for future reference to edit the files
copied_csv_paths = []

print(os.path.isdir(experiment_path_to_copy))
print(os.path.isdir(experiment_path_to_receive))

# first make the place where everything should be copied to

exp_to_name = os.path.split(experiment_path_to_copy)[-1]
exp_to_rece = os.path.split(experiment_path_to_receive)[-1]

Data_to_recieve = os.path.join(path_to_Data,exp_to_rece)
os.makedirs(Data_to_recieve,exist_ok = True)
os.makedirs(os.path.join(Data_to_recieve,'Groupnames'), exist_ok = True)
os.makedirs(os.path.join(Data_to_recieve,'divisions'),exist_ok = True)

# this sets up the individual -data folders to recieve the .csvs
temp = natsorted(glob.glob(os.path.join(experiment_path_to_receive,'*/')))
plates_to_receive = []
for this_folder in temp:
    if '-data' not in this_folder:
        plates_to_receive.append(this_folder)
plates_to_receive = natsorted(plates_to_receive)

plates_to_receive_data = []
for this_plate in plates_to_receive:
    if this_plate[-1] == '/':
        this_plate = this_plate[:-1]
    temp_path = this_plate + '-data'
    plates_to_receive_data.append(temp_path)
    os.makedirs(temp_path,exist_ok = True)

# this sets up the individual -data folders to send the .csvs
temp = natsorted(glob.glob(os.path.join(experiment_path_to_copy,'*/')))
plates_to_send_data = []
for this_folder in temp:
    if '-data' in this_folder:
        plates_to_send_data.append(this_folder)
plates_to_send_data = natsorted(plates_to_send_data)


# this actually send the division csv's to where they are supposed to go (unmodified)
for i,(this_plate_send,this_plate_receive) in enumerate(zip(plates_to_send_data,plates_to_receive_data)):

    csv_to_send = natsorted(glob.glob(os.path.join(this_plate_send,'*.csv')))[0]
    print(csv_to_send)

    print('BASIS OF DATA FOR v')

    csv_to_recieve_path = os.path.join(this_plate_receive,os.path.split(csv_to_send)[-1])
    print(csv_to_recieve_path)

    # actually copy it now to first the raw-data path
    # then to the _Data output paths 
    shutil.copy2(csv_to_send,csv_to_recieve_path)
    copied_csv_paths.append(csv_to_recieve_path)

    '''
        Cholesterol_screen_012-1_divisions.csv -> Cholesterol_screen_013-1_divisions.csv
    '''

    # this is to get the _Data pathing 
    temp_div_name = os.path.split(this_plate_receive)[-1].replace('-data','_divisions.csv')
    csv_to_recieve_path2 = os.path.join(Data_to_recieve,'divisions',temp_div_name)

    # copy it on over
    shutil.copy2(csv_to_send,csv_to_recieve_path2)
    copied_csv_paths.append(csv_to_recieve_path2)
    
    print('')

    pass

# this sends over the Groupname.csv to the _Data folder
assert(os.path.isfile(os.path.join(path_to_Data,exp_to_name,'Groupnames','Groupname.csv')))
# make the path
os.makedirs(os.path.join(path_to_Data,exp_to_rece,'Groupnames'),exist_ok=True)
# send her on over
shutil.copy2(os.path.join(path_to_Data,exp_to_name,'Groupnames','Groupname.csv'),
    os.path.join(path_to_Data,exp_to_rece,'Groupnames','Groupname.csv'))

copied_csv_paths.append(os.path.join(path_to_Data,exp_to_rece,'Groupnames','Groupname.csv'))

######
######
######

# this will individually open and replace each of the csvs that have been copied over
# with the paired replacements 

for this_csv_path in copied_csv_paths:

    print('\nEditing: ')
    print(this_csv_path)
    this_df = pd.read_csv(this_csv_path)

    temp_values_replaced = this_df.values

    # i know this is slow but idk how otherwise
    for this_replacement_pair in paired_replacements:
        for i,val_i in enumerate(temp_values_replaced):
            for j,val_j in enumerate(val_i):
                if this_replacement_pair[0] in str(val_j):
                    val_to_replace_with = temp_values_replaced[i,j].replace(this_replacement_pair[0],this_replacement_pair[1])
                    temp_values_replaced[i,j] = val_to_replace_with

    new_df = pd.DataFrame(temp_values_replaced, index=this_df.index, columns=this_df.columns)

    new_df.to_csv(this_csv_path,index = False,na_rep='NA')
    pass

print('EOF')