clear all
close all force hidden
warning('off', 'MATLAB:MKDIR:DirectoryExists');

% NOTE: the 95% confidense error bars are not the 'standard' error bars
% when using the combine_everything_into_one function

% get csv data file
[csv_file,csv_path] = uigetfile('*.csv','Please select the data file');

if ~isempty(csv_file) && ~isequal(csv_path,0)
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

% set the colormap from the number of isolated conditions
cmap = cmap_custom(conditions_to_isolate);

% regular not combinatorial
if ~combine_everything_into_one
    
    % set up variables
    keep_idx = cell(1,length(conditions_to_isolate));
    sep_exps_days = cell(1,length(conditions_to_isolate));
    sep_exps_days_health = cell(1,length(conditions_to_isolate));
    censored_wells_any_separated = cell(1,length(conditions_to_isolate));
    legend_names = cell(1,length(conditions_to_isolate));
    legend_names_health = cell(1,length(conditions_to_isolate));
    median_lifespans = zeros(1,length(conditions_to_isolate));
    median_healthspans = zeros(1,length(conditions_to_isolate));
    N = zeros(1,length(conditions_to_isolate));
    C = zeros(1,length(conditions_to_isolate));
    
    % isolate the ones that you want
    % and other associated variables
    
    for i = 1:length(conditions_to_isolate)
        % find specific idx that represent that condition
        keep_idx{i} = (condition_comb == conditions_to_isolate(i));
        
        % get life and healthspan from dataset
        sep_exps_days{i} = data.("Last day of observation")(keep_idx{i});
        sep_exps_days_health{i} = data.("Last day of health")(keep_idx{i});
        
        % get the censors
        censored_wells_any_separated{i} = [data.("Manual Censor")(keep_idx{i}) | ...
            data.("Runoff Censor experiment")(keep_idx{i}) | ...
            data.("Runoff Censor inital")(keep_idx{i})];
                
        % get the median life and healthspans
        median_lifespans(i) = ...
            calculate_median_of_ecdf(sep_exps_days{i},...
            censored_wells_any_separated{i});
        median_healthspans(i) = ...
            calculate_median_of_ecdf(sep_exps_days_health{i},...
            censored_wells_any_separated{i});

        % get the total N values
        N(i) = sum(keep_idx{i}); % - sum(censored_wells_any_separated{i});
        
        C(i) = sum(censored_wells_any_separated{i});
        
        legend_names{i} = [conditions_to_isolate{i} ...
            ' | median lifespan: ' num2str(median_lifespans(i)) ...
            ' | N=' num2str(N(i))...
            ' | C=' num2str(C(i))];
        
        legend_names_health{i} = [conditions_to_isolate{i} ...
            ' | median healthspan: ' num2str(median_healthspans(i)) ...
            ' | N=' num2str(N(i))...
            ' | C=' num2str(C(i))];
        
    end
else
    
    conditions_to_isolate_temp = conditions_to_isolate;
    for i = 1:length(conditions_to_isolate)
        conditions_to_isolate_temp(i) = string(['-- ' char(conditions_to_isolate(i))]);
    end
    combined_experiments = all_exp_cond(contains(all_exp_cond,conditions_to_isolate_temp))';
    
    % this is for comparing single conditions across experiments
    
    % set up variables
    % set up variables
    keep_idx = cell(1,length(combined_experiments)+1);
    sep_exps_days = cell(1,length(combined_experiments)+1);
    sep_exps_days_health = cell(1,length(combined_experiments)+1);
    censored_wells_any_separated = cell(1,length(combined_experiments)+1);
    legend_names = cell(1);
    legend_names_health = cell(1);
    median_lifespans = zeros(1);
    median_healthspans = zeros(1);
    N = zeros(1);
    
    % isolate the ones that you want
    % and other associated variables
    
    keep_idx_temp = zeros(1,height(data));
    
    for i = 1:length(combined_experiments)
        keep_idx_temp = keep_idx_temp + (experiment_condition_comb == combined_experiments(i));
    end
    
    % conbine the keep idx
    keep_idx_final = logical(keep_idx_temp);
    
    % rename the conditions to the name of the test
    experiments_to_isolate_comb = name_of_test;
    
    for i = 1:length(combined_experiments)
        % find specific idx that represent that condition
        keep_idx{i} = (experiment_condition_comb == combined_experiments(i));
        
        % get life and healthspan from dataset
        sep_exps_days{i} = data.("Last day of observation")(keep_idx{i});
        sep_exps_days_health{i} = data.("Last day of health")(keep_idx{i});
        
        % get the censors
        censored_wells_any_separated{i} = [data.("Manual Censor")(keep_idx{i}) | ...
            data.("Runoff Censor experiment")(keep_idx{i}) | ...
            data.("Runoff Censor inital")(keep_idx{i})];
        
    end
    
    i = 1;
    
    % get all the data as a pooled set
    sep_exps_days{end} = data.("Last day of observation")(keep_idx_final);
    sep_exps_days_health{end} = data.("Last day of health")(keep_idx_final);
    
    censored_wells_any_separated{end} = [data.("Manual Censor")(keep_idx_final) | ...
        data.("Runoff Censor experiment")(keep_idx_final) | ...
        data.("Runoff Censor inital")(keep_idx_final)];
        
    % get the median life and healthspans
    median_lifespans(i) = ...
        calculate_median_of_ecdf(sep_exps_days{end},...
        censored_wells_any_separated{end});
    median_healthspans(i) = ...
        calculate_median_of_ecdf(sep_exps_days_health{end},...
        censored_wells_any_separated{end});
    
    N(i) = sum(keep_idx_final); % - sum(censored_wells_any_separated{i});
    
    C(i) = sum(censored_wells_any_separated{end});
    
    legend_names{i} = [experiments_to_isolate_comb ...
        ' | median lifespan: ' num2str(median_lifespans(i)) ...
        ' | N=' num2str(N(i))...
        ' | C=' num2str(C(i))];
    
    legend_names_health{i} = [experiments_to_isolate_comb ...
        ' | median healthspan: ' num2str(median_healthspans(i)) ...
        ' | N=' num2str(N(i))...
        ' | C=' num2str(C(i))];
    
end

% find the maximum number of days survived from the entire experiment
max_days = max(cellfun(@max,sep_exps_days));


if ~combine_everything_into_one
    % plot the lifespan survival curves
    plot_survival_curve_life(conditions_to_isolate,...
        sep_exps_days,censored_wells_any_separated,legend_names,...
        max_days,name_of_exp,use_markers,use_title,cmap,font_size,csv_path,...
        save_plots)
    
    % plot the healthspan survival curves
    plot_survival_curve_health(conditions_to_isolate,...
        sep_exps_days_health,censored_wells_any_separated,legend_names_health,...
        max_days,name_of_exp,use_markers,use_title,cmap,font_size,csv_path,...
        save_plots)
else
    % plot the lifespan survival curves
    plot_survival_curve_life_combine(combined_experiments,...
        sep_exps_days,censored_wells_any_separated,legend_names,...
        max_days,name_of_exp,use_markers,use_title,font_size,csv_path,...
        save_plots);
    
    % plot the healthspan survival curves
    plot_survival_curve_health_combine(combined_experiments,...
        sep_exps_days_health,censored_wells_any_separated,legend_names_health,...
        max_days,name_of_exp,use_markers,use_title,font_size,csv_path,...
        save_plots);
end

out_folder = fullfile(csv_path,[name_of_exp '_lifespan.png']);

if save_plots
    if ispc
        cmd_command = ['explorer /select, ' out_folder];
        system(cmd_command);
    else
        out_folder = fileparts(replace(out_folder,' ', '\ '));
        terminal_command = ['open -R ' out_folder];
        
        [status,cmdout] = system(terminal_command);
        
        if status ~= 0 
            [status,cmdout] = system(['gio open ' out_folder]);
        end
    end
end

size_of_graph = 2000;

% set up a couple new features
% combined contions and total movement
variable_names = data.Properties.VariableNames;
idx_activity = contains(variable_names,'daily_activity_combined');
idx_healthspan = strcmp(variable_names,"Last day of health");
idx_lifepsan = strcmp(variable_names,"Last day of observation");


% input the new features
data.("Total activity") = sum(table2array(data(:,idx_activity)),2);
data.Condition = condition_comb;
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

mkdir(fullfile(csv_path,'activity_groupings'));
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
    
    g.WindowState = 'maximized';
    
    this_condition_unique = replace(condition_unique(i),{'/','\'},'-per-');
    
    if save_plots
        saveas(g,fullfile(pwd,'output_figures',[exp_nm 'activity_' char(this_condition_unique) '.png']))
        saveas(g,fullfile(csv_path,'activity_groupings',[exp_nm 'activity_' char(this_condition_unique) '.png']));
    end
    
end

close all

plot_mean_activites(good_data,conditions_to_isolate,exp_nm,csv_path,csv_file,0,cmap,idx_activity)
plot_mean_activites(good_data,conditions_to_isolate,exp_nm,csv_path,csv_file,1,cmap,idx_activity)

close all

disp('Finished with no errors')

function this_median = calculate_median_of_ecdf(sep_exps_days,censored_wells_any_separated)

[this_survival_curve,x] = ecdf(sep_exps_days,...
    'censoring',censored_wells_any_separated,'function','survivor');

duplicated_numbers = (diff(x)==0);

interp_x = min(x):0.5:max(x);

interp_survival_curve = interp1(x(~duplicated_numbers),...
    this_survival_curve(~duplicated_numbers),interp_x);

[~,min_idx] = min(abs(interp_survival_curve-0.5));

this_median = round(interp_x(min_idx));

end

function plot_survival_curve_life(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,colors_to_plot,font_size,csv_path,...
    save_plots)

% This is an un-elegant solution for the problem that you cant just
% plot many different lines without them all being the same color and style
all_marks = {'o','+','*','.','x','s','d','^','p','h','o','+','*',...
    '.','x','s','d','^','p','h','o','+','*','.','x','s','d','^',...
    'p','h','o','+','*','.','x','s','d','^','p','h'};

% color_idx = round(linspace(1,256,length(conditions)));
% colors_to_plot = cmap(color_idx,:);
% colors_to_plot(1,:) = [0,0,0];

% create the fullscreen figure
g = figure('units','normalized','outerposition',[0 0 1 1]);
% increase the axis font size
axes('FontSize',20)
% make sure the graph is square
axis square
hold on
for i = 1:length(conditions)
    % get the ecdf survival curves
    [this_survival_curve,x] = ecdf(days_survived{i},...
        'censoring',censor{i},'function','survivor');
    
    % plot the specific curve with colors and sizes
    if use_markers
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',colors_to_plot(i,:),'Marker',all_marks{i},'MarkerSize',10)
    else
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',colors_to_plot(i,:))
    end
end

% labels and legends
if use_title
    title(['Combined lifespans for ' name_of_exp],'Interpreter','none','FontSize',24);
end
ylabel('Fraction remaining','FontSize',20,'FontWeight','bold')
xlabel('Days on robot','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

% save to a folder in output_figures
mkdir(fullfile(pwd,'output_figures'))

this_name_of_exp = replace(name_of_exp,{'/','\'},'-per-');

if save_plots
    saveas(g,fullfile(pwd,'output_figures',[this_name_of_exp '_lifespan.png']))
    saveas(g,fullfile(csv_path,[this_name_of_exp '_lifespan.png']));
end

hold off


end

function plot_survival_curve_health(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,colors_to_plot,font_size,csv_path,...
    save_plots)

% see plot_survival_curve_life for detailed notes

all_marks = {'o','+','*','.','x','s','d','^','p','h','o','+','*',...
    '.','x','s','d','^','p','h','o','+','*','.','x','s','d','^',...
    'p','h','o','+','*','.','x','s','d','^','p','h'};

% color_idx = round(linspace(1,256,length(conditions)));
% colors_to_plot = cmap(color_idx,:);
% colors_to_plot(1,:) = [0,0,0];

g = figure('units','normalized','outerposition',[0 0 1 1]);
axes('FontSize',20)
axis square
hold on
for i = 1:length(conditions)
    [this_survival_curve,x] = ecdf(days_survived{i},...
        'censoring',censor{i},'function','survivor');
    if use_markers
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',colors_to_plot(i,:),'Marker',all_marks{i},'MarkerSize',10)
    else
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',colors_to_plot(i,:))
    end
end

if use_title
    title(['Combined healthspans for ' name_of_exp],'Interpreter','none','FontSize',24);
end
ylabel('Fraction healthy','FontSize',20,'FontWeight','bold');
xlabel('Days healthy on robot','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

this_name_of_exp = replace(name_of_exp,{'/','\'},'-per-');

if save_plots
    saveas(g,fullfile(pwd,'output_figures',[this_name_of_exp '_healthspan.png']))
    saveas(g,fullfile(csv_path,[this_name_of_exp '_healthspan.png']));
end

hold off


end




function [g] = plot_survival_curve_life_combine(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,font_size,csv_path,...
    save_plots)

% This is an un-elegant solution for the problem that you cant just
% plot many different lines without them all being the same color and style

% create the fullscreen figure
g = figure('units','normalized','outerposition',[0 0 1 1]);
% increase the axis font size
axes('FontSize',20)
% make sure the graph is square
axis square
hold on

ecdf_matrix = zeros(length(days_survived)-1,max(cellfun(@max,days_survived)));

for i = 1:length(conditions)+1
    % get the ecdf survival curves
    [this_survival_curve,x,flo,fup] = ecdf(days_survived{i},...
        'censoring',censor{i},'function','survivor');
    
    ecdf_matrix(i,1:length(this_survival_curve)) = this_survival_curve;
    
    % plot the specific curve with colors and sizes
    
    if isequal(i,length(conditions)+1)
        
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color','k')
        
    else
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',[0.5,0.5,0.5,0.2])
    end
end

% labels and legends
if use_title
    title(['Combined lifespans for ' name_of_exp],'Interpreter','none','FontSize',24);
end
ylabel('Fraction remaining','FontSize',20,'FontWeight','bold')
xlabel('Days on robot','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

% save to a folder in output_figures
mkdir(fullfile(pwd,'output_figures'))

this_name_of_exp = replace(name_of_exp,{'/','\'},'-per-');

if save_plots
    saveas(g,char(fullfile(pwd,'output_figures',[this_name_of_exp '_lifespan.png'])));
    saveas(g,fullfile(csv_path,[this_name_of_exp '_lifespan.png']));
end

hold off

end

function plot_survival_curve_health_combine(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,font_size,csv_path,...
    save_plots)

% see plot_survival_curve_life for detailed notes

g = figure('units','normalized','outerposition',[0 0 1 1]);

axes('FontSize',20)
axis square
hold on
for i = 1:length(conditions)+1
    [this_survival_curve,x,flo,fup] = ecdf(days_survived{i},...
        'censoring',censor{i},'function','survivor');
    
    if isequal(i,length(conditions)+1)
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color','k')
        
%         stairs(x,flo,...
%             'LineStyle','--','LineWidth',2,...
%             'Color','k')
%         stairs(x,fup,...
%             'LineStyle','--','LineWidth',2,...
%             'Color','k')
    else
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color',[0.5,0.5,0.5,0.2])
    end
end

if use_title
    title(['Combined healthspans for ' name_of_exp],'Interpreter','none','FontSize',24);
end
ylabel('Fraction healthy','FontSize',20,'FontWeight','bold');
xlabel('Days healthy on robot','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

this_name_of_exp = replace(name_of_exp,{'/','\'},'-per-');

if save_plots
    saveas(g,char(fullfile(pwd,'output_figures',[this_name_of_exp '_healthspan.png'])));
    saveas(g,fullfile(csv_path,[this_name_of_exp '_healthspan.png']));
end

hold off


end



function cmap_out = cmap_custom(conditions_to_isolate)

% base colors, black, red, blue, green, orange
base_colors = ...
    [0,0,0;... % black
    1,0,0;... % red
    0,0,1;... % blue
    1,0.65,0;... % orange
    0,1,1;... % cyan
    1,0,1; % purple
    1,0.85,0;... % yellow orange 
    0.54,0.27,0.07; % brown 
    0,1,0;... % green
    ];

num_base_colors = size(base_colors,1);

num_conditions = length(conditions_to_isolate);

if num_conditions <= num_base_colors
    disp('Base colormap used')
    cmap_out = base_colors(1:num_conditions,:);
else
    disp('More than standard colormap used')
    cmap_out = colormap(linspecer(length(conditions_to_isolate)));
    cmap_out(1,:) = zeros(size(cmap_out(1,:)));
end

% good maps 'jet' 'winter' 'hot' 'hsv' 'parula' 'cool' 'turbo'
close all

end

function X_out = seperate_string_array(X_in,this_delimiter)

if ~isstring(X_in)
    X_in = string(X_in);
end

if ~(exist('this_delimiter','var'))
    this_delimiter = {',',' '};
end

for i = 1:length(X_in)
    temp_str = strsplit(X_in(i), this_delimiter);
    
    for j = 1:length(temp_str)
        X_mid(i,j) = temp_str(j);
    end
    
end

X_out = X_mid;

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

y = linspace(0,size_of_graph,length(this_life)+1);
x = linspace(0,size_of_graph,num_days_experiment_ran+1);

for i = 1:length(y)-1
    y2(i) = mean([y(i),y(i+1)]);
end
for i = 1:length(x)-1
    x2(i) = mean([x(i),x(i+1)]);
end

still_alive = this_life>length(x2);

if sum(still_alive) == 0
    this_life_x = x2(nonzeros(this_life.*(this_life>0)));
    this_life_y = y2(nonzeros((1:length(this_life))'.*(this_life>0)));
    
    this_life_x = [this_life_x(1),this_life_x,this_life_x(end)];
    this_life_y = [0,this_life_y,size_of_graph];
else
    this_life2 = this_life;
    this_life2(this_life2>length(x2)) = 0;
    
    this_life_x = x2(nonzeros(this_life2.*(this_life2>0)));
    this_life_y = y2(nonzeros((1:length(this_life2))'.*(this_life2>0)));
    
    endpoint_x = this_life_x(end);
    endpoint_y = ((this_life_y(2)-this_life_y(1))/2)+this_life_y(end);
    
    this_life_x = [this_life_x(1),this_life_x,endpoint_x];
    this_life_y = [0,this_life_y,endpoint_y];
end

% make sure that it doesnt overflow
if sum(this_health>length(x2))
    this_health(this_health>length(x2)) = length(x2);
end

this_health_x =  x2(nonzeros(this_health.*(this_health>0)));
this_health_y =  y2(nonzeros((1:length(this_health))'.*(this_health>0)));

stairs(this_life_x,this_life_y,'LineStyle','-','LineWidth',5,'Color','r')
plot(this_health_x,this_health_y,'gs')

axis on
xticks([1,round(size_of_graph/4),round(size_of_graph/2),round(size_of_graph*(3/4)),size_of_graph]); 
xticklabels({num2str(0),num2str(num_days_experiment_ran/4),...
    num2str(num_days_experiment_ran/2),num2str(num_days_experiment_ran*(3/4)),num2str(num_days_experiment_ran)})
yticks([1, round(size_of_graph/2),size_of_graph]); 
yticklabels({num2str(1),num2str(round(num_worms/2)),num2str(num_worms)})

xlabel('Days on the robotic system')
ylabel('Individual animals')


hold off

end

function plot_mean_activites(good_data,conditions_to_isolate,exp_nm,csv_path,~,smooth_bool,cmap,idx_activity)

g2 = figure('units','normalized','outerposition',[0 0 1 1]);
hold on
for i = 1:length(conditions_to_isolate)
    
    this_condition_idx = (good_data.Condition == conditions_to_isolate(i));
    
    this_data = good_data(this_condition_idx,:);
    
    this_activity = table2array(this_data(:,idx_activity));
    this_activity = clean_this_activity(this_activity,this_data);
    
    this_activity_norm_mean = mean(this_activity);
    this_activity_norm_mean_filt = medfilt1(this_activity_norm_mean,3);
    if smooth_bool
        this_activity_norm_mean_filt = smoothdata(this_activity_norm_mean_filt,'gaussian');
    end
    
    if isequal(i,1)
        running_max = max(this_activity_norm_mean_filt,[],'all');
    else
        if running_max < max(this_activity_norm_mean_filt,[],'all')
            running_max = max(this_activity_norm_mean_filt,[],'all');
        end
    end
    
    x = 1:length(this_activity_norm_mean_filt);
    
    plot(x,this_activity_norm_mean_filt,'Color',cmap(i,:),'LineWidth',5)
    
end
pause(0.1)
title('Mean activities over time per condition')
axis square 
ylabel('Normalized Activity')
xlabel('Days on robot')
ylim([0,running_max])
yticks([1, round(running_max/2),running_max]); 
yticklabels({num2str(0),num2str(0.5),num2str(1)})
legend(conditions_to_isolate);

if smooth_bool
    saveas(g2,fullfile(csv_path,['activity_norm_smooth_' char(exp_nm) '.png']));
else
    saveas(g2,fullfile(csv_path,['activity_norm_' char(exp_nm) '.png']));
end

end