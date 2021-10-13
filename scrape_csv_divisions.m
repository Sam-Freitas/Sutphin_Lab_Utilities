
WW_data_path = '/Volumes/WormWatcher/_Data';

% exp_data_path = uigetdir(WW_data_path,'select folder containing the csv');

exp_data_dir = dir(fullfile(exp_data_path,'*.csv'));

csv_table = readtable(fullfile(exp_data_dir.folder,exp_data_dir.name),'VariableNamingRule','preserve');

[~,exp_name,~]=fileparts(exp_data_dir.name);

unique_plate_ID = unique(string(csv_table.("Plate ID")));
plate_ID = string(csv_table.("Plate ID"));

header = ["Well Location", "Dosage","Strain"];

full_division = [convert_double_array_to_cell(csv_table.("Well Location"))...
    ,csv_table.Dosage,csv_table.Strain];


mkdir('output_csvs');
mkdir(fullfile('output_csvs',exp_name));

for i = 1:length(unique_plate_ID)
    
    this_idx = (plate_ID == unique_plate_ID(i));
    
    this_division = full_division(this_idx,:);
    
    this_plate_name = [char(unique_plate_ID(i)) '_divisions.csv'];
    
    out_path = fullfile(pwd,fullfile('output_csvs',exp_name),this_plate_name);
    
    T = cell2table(this_division,'VariableNames',header);
    
    writetable(T,out_path);
end



function out_cell_array = convert_double_array_to_cell(in_array)


out_cell_array = cell(size(in_array));
for i = 1:length(in_array)
    
    out_cell_array{i} = in_array(i);
    
end

end