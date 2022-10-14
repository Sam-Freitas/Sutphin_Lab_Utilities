clear all
close all force hidden

data_path = "Z:\_Data";

data_dir = dir(fullfile(data_path));

is_dir_flag = cell2mat({data_dir.isdir});

data_dir = data_dir(is_dir_flag);
data_dir(ismember( {data_dir.name},{'..','.','Old_data','Sutphin_Lab_Utilities','output_figures','Compiled_table','test'})) = [];

output = cell(1,2);
count = 1;
for i = 1:length(data_dir)
    this_data_path = fullfile(data_path,data_dir(i).name);
    this_data_csv_dir = dir(fullfile(this_data_path,'*.csv'));

    if ~isempty(this_data_csv_dir) && isequal(length(this_data_csv_dir),1)
        output{count,1} = this_data_csv_dir.name;
        output{count,2} = this_data_csv_dir.date;

        count = count +1;
    end
end

header = ["name","date processed (m/d/y)"];
T = cell2table(output,"VariableNames",header);

writetable(T,'Data_dates.csv')







