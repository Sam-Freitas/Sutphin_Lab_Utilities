% this script scrapes the processed csv's from the _Data folder then
% outputs the dates
clear all
close all force hidden

data_path = "Z:\_Data";
trust_data = '2021-05-01'; % yyyy-MM-dd

data_dir = dir(fullfile(data_path));

is_dir_flag = cell2mat({data_dir.isdir});

data_dir = data_dir(is_dir_flag);
data_dir(ismember( {data_dir.name},{'..','.','Old_data','Sutphin_Lab_Utilities','output_figures','Compiled_table','test'})) = [];

output = cell(1,2);
count = 1;
for i = 1:length(data_dir)
    this_data_path = fullfile(data_path,data_dir(i).name);
    this_data_groupname_path = fullfile(this_data_path,'Groupnames','Groupname.csv');
    this_data_csv_dir = dir(fullfile(this_data_path,'*.csv'));

    if ~isempty(this_data_csv_dir) && isequal(length(this_data_csv_dir),1)
        output{count,1} = this_data_csv_dir.name;
        this_processd_date = datetime(this_data_csv_dir.date);
        this_processd_date.Format = 'yyyy-MMM-dd';
        output{count,2} = char(this_processd_date);
%         output{count,3} = this_data_csv_dir.datenum;

        if isfile(this_data_groupname_path)
            this_groupname = readtable(this_data_groupname_path,'VariableNamingRule','preserve','ReadRowNames',1);
            robot_idx = contains(this_groupname.Properties.RowNames,'robot');
            date_put_on_robot = string(table2cell(this_groupname(robot_idx,1)));
            date_put_on_robot = datetime(date_put_on_robot,'InputFormat','yyyy-MM-dd');
            date_put_on_robot.Format = 'yyyy-MMM-dd';
            output{count,3} = char(date_put_on_robot);
        else
            output{count,4} = 'Yes';
        end

        count = count +1;
    end
end

[~,idx] = sort(datetime(output(:,2),'InputFormat','yyyy-MMM-dd'));
output = output(idx,:);

header = ["name","date processed (yyyy/MM/dd)",...
    "Date of experiment (yyyy/MM/dd)","missing groupname"];
T = cell2table(output,"VariableNames",header);

writetable(T,'Data_dates.csv')







