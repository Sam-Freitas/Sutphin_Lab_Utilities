clear all
close all force hidden
warning('off', 'MATLAB:MKDIR:DirectoryExists');

% NOTE: the 95% confidense error bars are not the 'standard' error bars
% when using the combine_everything_into_one function

% get csv data file
[csv_file,csv_path] = uigetfile('*.csv','Please select the data file');

if ~isempty(csv_file)
    data = readtable(fullfile(csv_path,csv_file),...
        'VariableNamingRule','preserve');
    [~,exp_nm,~] = fileparts(csv_file);
    
else
    error('Please give the .csv for the experiment');
end

% User input choice
prompt = {'Name of the Experiment? - leave blank for default:', ...
    'Use markers in plot? 0 (default) no, 1 yes:',...
    'Use title on plot? 0 (default) no, 1 yes:',...
    'Font size?:',...
    'Sorting by (1) Strain (0) Condition',...
    'Compile selection into single experiment? 0 (default) no, 1 yes',...
    'Testing mode, dont save plots (0), save plots (1)'};
dlgtitle = 'User Inputs for Lightsaver';
dims = [1 100];
definput = {'','0','0','11','1','0','1'};
answer = inputdlg(prompt,dlgtitle,dims,definput);

if isempty(answer)
    error('Please select user inputs')
end

name_of_test = char(answer{1});
use_markers = str2double(answer{2});
use_title = str2double(answer{3});
font_size = str2double(answer{4});
sorting_group = str2double(answer{5});
combine_everything_into_one = str2double(answer{6});
save_plots = str2double(answer{7});

% check and parse
if ~isempty(name_of_test)
    
    default_name = 0;
    
    name_of_exp = name_of_test;

    if contains(name_of_exp,{'/','\'})
        disp([name_of_exp 'contains slashes, replacing with -per-']);
        name_of_exp = replace(name_of_exp,{'/','\'},'-per-');
    end
else
    default_name = 1;
end

if isequal(default_name,1)
    name_of_test = {exp_nm};
    name_of_exp = exp_nm;
end

% get data
condition_cell = data.Groupname;
condition_comb = string(condition_cell);

% reference for all the conditions
all_cond = string(natsort(cellstr(unique(condition_comb))));


% select the conditions that you want
[choice_idx,tf] = listdlg('ListString',all_cond,...
    'PromptString','Select conditions to plot','ListSize',[500 500]);

if isempty(choice_idx)
    error('Please choose at least one condition')
end

% if you are not combining everything
% then get the control for that experiment
if ~combine_everything_into_one
    [control_indx,tf] = listdlg('PromptString',{'Select the Control.',...
        'Only one Control can be selected.',''},...
        'SelectionMode','single','ListString',all_cond(choice_idx),...
        'ListSize',[500 500]);
    
    temp_choice = choice_idx(control_indx);
    
    choice_idx(control_indx) = [];
    
    choice_idx = [temp_choice, choice_idx];
end

% isolate the conditions from all the conditions
conditions_to_isolate = all_cond(choice_idx);

data = readtable('data2.csv','VariableNamingRule','preserve');
data_duplicate = data;

size_of_graph = 2000;

% set up a couple new features
% combined contions and total movement
variable_names = data.Properties.VariableNames;
idx_activity = contains(variable_names,'daily_activity');
idx_healthspan = strcmp(variable_names,"Last day of health");
idx_lifepsan = strcmp(variable_names,"Last day of observation");

condition_cell = [data.Dosage, data.Strain];
condition_comb = strings(1,length(condition_cell));
for i = 1:length(condition_cell)
    condition_comb(i) = string([condition_cell{i,1} ' -- ' condition_cell{i,2}]);
end

% input the new features
data.("Total activity") = sum(table2array(data(:,idx_activity)),2);
data.Condition = condition_comb';
data.("Combined metric") = table2array(data(:,idx_healthspan)) + table2array(data(:,idx_lifepsan));

condition_unique = unique(condition_comb);

variable_names = data.Properties.VariableNames;

idx_healthspan = strcmp(variable_names,"Last day of health");
idx_lifepsan = strcmp(variable_names,"Last day of observation");
idx_death_detected = strcmp(variable_names,"Death Detected");
idx_activity = contains(variable_names,'daily_activity_combined');
idx_combined_metric = contains(variable_names,'Combined metric');

col_healthspan = nonzeros((1:size(data,2)).*idx_healthspan);
col_lifespan = nonzeros((1:size(data,2)).*idx_lifepsan);
col_death_detected = nonzeros((1:size(data,2)).*idx_death_detected);
col_combined_metric = nonzeros((1:size(data,2)).*idx_combined_metric);

data_activity = table2array(data(:,idx_activity));
data_healthspan = table2array(data(:,idx_healthspan));
data_lifespan = table2array(data(:,idx_lifepsan));
data_total_activity = sum(data_activity,2);
data_death_detected = table2array(data(:,idx_death_detected));

col_total_activity = size(data,2);

num_days_experiment_ran = sum(idx_activity);

sorting_array = [data_lifespan,data_healthspan,data_total_activity,data_death_detected];

[sorted_data,idx_sort] = sortrows(data,[col_death_detected,col_lifespan,col_combined_metric]);

good_data = sorted_data((sorted_data.("Death Detected") == 1),:);
good_data = good_data((good_data.("Last day of observation") > 1),:);

overall_max_activity = max(max(table2array(good_data(:,idx_activity))));

max_activity_per_animal = max(table2array(good_data(:,idx_activity)),[],2);
good_enough_max_activity = mean(max_activity_per_animal)+3*std(max_activity_per_animal);


for i = 1:length(condition_unique)
    
    this_condition_idx = (good_data.Condition == condition_unique(i));
    
    this_data = good_data(this_condition_idx,:);
    
    this_activity = table2array(this_data(:,idx_activity));
    this_activity = clean_this_activity(this_activity,this_data);
    this_activity = resize_and_reshape_activity(this_activity,size_of_graph);
        
    g = figure('units','normalized','outerposition',[0 0 1 1]);
    imshow(this_activity,[0 good_enough_max_activity]);
    colormap(g,'parula')
    pause(.1)
    colorbar('FontSize',12);
    pause(.1)
    
    plot_this_healthspan_lifespan_on_activity(table2array(this_data(:,idx_lifepsan))...
        ,table2array(this_data(:,idx_healthspan)),...
        num_days_experiment_ran,size_of_graph)
    
    title(condition_unique(i),'Interpreter','None')
    
end





function this_activity = clean_this_activity(this_activity,this_data)

end_of_life = this_data.("Last day of observation");

for i = 1:size(this_activity,1)
    
    this_activity(i,end_of_life(i):end) = 0;
    
end

end

function this_activity = resize_and_reshape_activity(this_activity,size_of_graph)

a = imresize(this_activity, [size_of_graph, size(this_activity,2)],'nearest');
a = imresize(a,[size_of_graph,size_of_graph]);

this_activity = a;

end


function plot_this_healthspan_lifespan_on_activity(this_life,this_health,...
    num_days_experiment_ran,size_of_graph)

hold on

num_worms = length(this_life);

y = linspace(0,size_of_graph,length(this_life));
x = linspace(0,size_of_graph,num_days_experiment_ran);

for i = 1:length(this_life)
    
    if this_life(i) > 0
        plot(x(this_life(i)),y(i),'ro')
    end
    if this_health(i) > 0
        plot(x(this_health(i)),y(i),'go')
    end
    
end

axis on
xticks([1, round(size_of_graph/2),size_of_graph]); 
xticklabels({num2str(0),num2str(num_days_experiment_ran/2),num2str(num_days_experiment_ran)})
yticks([1, round(size_of_graph/2),size_of_graph]); 
yticklabels({num2str(1),num2str(round(num_worms/2)),num2str(num_worms)})

xlabel('Days on the robotic system')
ylabel('Individual animals')


hold off

end

