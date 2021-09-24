clear all
close all force hidden
warning('off', 'MATLAB:MKDIR:DirectoryExists');

curr_dir = dir(fullfile(pwd,'*'));
curr_dir = curr_dir([curr_dir.isdir]);

curr_dir=curr_dir(~ismember({curr_dir.name},{'.','..'}));

fails = strings(1);
fail_counter = 1;

for i = 1:length(curr_dir)
    
    close all force hidden
    
    this_dir = dir(fullfile(curr_dir(i).folder,curr_dir(i).name));
    
    names = string({this_dir.name});
    
    [~,~,exts] = fileparts(names);
    
    csv_idx = find(exts == ".csv",1,'first');
    
    if ~isempty(csv_idx)
        
        csv_file = this_dir(csv_idx).name;
        csv_path = this_dir(csv_idx).folder;
        try
            plot_this_exp(csv_file,csv_path)
        catch
            disp(['failed on ' char(csv_file)])
            fails(fail_counter) = string(csv_file);
            fail_counter = fail_counter +1;
        end
    
    end
    
end

disp(fails)


function plot_this_exp(csv_file,csv_path)

% NOTE: the 95% confidense error bars are not the 'standard' error bars
% when using the combine_everything_into_one function

% unless you have more than 5/6 different conditions
% dont use markers they look bad
use_markers = 0;

% Generally titles are not necessary in published figures;
use_title = 0;

% only used for combining single conditions across multiple experiments
combine_everything_into_one = 0;

default_name = 1;

% get name of test
if isequal(default_name,0)
    name_of_test = inputdlg('What is the name of this test?');
    
    % check and parse
    if ~isempty(name_of_test)
        name_of_exp = name_of_test{1};
    else
        error('Please input name for the experiment');
    end
    
end

font_size = 11;

if ~isempty(csv_file)
    data = readtable(fullfile(csv_path,csv_file),...
        'VariableNamingRule','preserve');
    [~,exp_nm,~] = fileparts(csv_file);
    
    if isequal(default_name,1)
        name_of_test = {exp_nm};
        name_of_exp = exp_nm;
    end
    
else
    error('Please give the .csv for the experiment');
end

% get data
condition_cell = [data.Dosage, data.Strain];
condition_comb = strings(1,length(condition_cell));

% combine the strings
for i = 1:length(condition_cell)
    condition_comb(i) = string([condition_cell{i,1} ' -- ' condition_cell{i,2}]);
end

% reference for all the conditions
all_cond = unique(condition_comb);

% if wnat to do by plate just add data.("Plate ID") then update line 57
try
    experiment_condition_cell = [data.("Experiment Name"), data.Dosage, data.Strain];
    experiment_condition_comb = strings(1,length(experiment_condition_cell));
catch
    data.("Experiment Name") = repmat({exp_nm},size(data.("Worm number")));
    experiment_condition_cell = [data.("Experiment Name"), data.Dosage, data.Strain];
    experiment_condition_comb = strings(1,length(experiment_condition_cell));
end

% combine the strings
for i = 1:length(experiment_condition_cell)
    experiment_condition_comb(i) = string([experiment_condition_cell{i,1} ' -- ' ...
        experiment_condition_cell{i,2} ' -- ' experiment_condition_cell{i,3}]);
end

% reference for all the experiments
all_exp_cond = unique(experiment_condition_comb);

all_cond_cell = cell(1,length(all_cond));
for i = 1:length(all_cond)
    all_cond_cell{i} = char(all_cond(i));
end

[~,natsort_idx,~] = natsort(all_cond_cell);

all_cond = all_cond(natsort_idx);

% % select the conditions that you want
% [choice_idx,tf] = listdlg('ListString',all_cond);
% 
% if isempty(choice_idx)
%     error('Please choose at least one condition')
% end
% 
% % if you are not combining everything
% % then get the control for that experiment
% if ~combine_everything_into_one
%     [control_indx,tf] = listdlg('PromptString',{'Select the Control.',...
%         'Only one Control can be selected.',''},...
%         'SelectionMode','single','ListString',all_cond(choice_idx));
%     
%     temp_choice = choice_idx(control_indx);
%     
%     choice_idx(control_indx) = [];
%     
%     choice_idx = [temp_choice, choice_idx];
% end

% isolate the conditions from all the conditions
% conditions_to_isolate = all_cond(choice_idx);
conditions_to_isolate = all_cond;

for i = 1:length(conditions_to_isolate)
    len_conds(i) = length(char(conditions_to_isolate(i)));
end

contains_control = contains(lower(conditions_to_isolate),"control");

if sum(contains_control) == 0
    contains_control = contains(lower(conditions_to_isolate),"ev");
end

sort_cols = [~contains_control',len_conds'];

[~,control_indx] = sortrows(sort_cols,[1,2]);

temp_choice = conditions_to_isolate(control_indx);

conditions_to_isolate(control_indx) = [];

conditions_to_isolate = [temp_choice, conditions_to_isolate];

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
    
    legend_names{i} = [experiments_to_isolate_comb{i} ...
        ' | median lifespan: ' num2str(median_lifespans(i)) ...
        ' | N=' num2str(N(i))...
        ' | C=' num2str(C(i))];
    
    legend_names_health{i} = [experiments_to_isolate_comb{i} ...
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
        max_days,name_of_exp,use_markers,use_title,cmap,font_size,csv_path)
    
    % plot the healthspan survival curves
    plot_survival_curve_health(conditions_to_isolate,...
        sep_exps_days_health,censored_wells_any_separated,legend_names_health,...
        max_days,name_of_exp,use_markers,use_title,cmap,font_size,csv_path)
else
    % plot the lifespan survival curves
    plot_survival_curve_life_combine(combined_experiments,...
        sep_exps_days,censored_wells_any_separated,legend_names,...
        max_days,name_of_exp,use_markers,use_title,font_size,csv_path);
    
    % plot the healthspan survival curves
    plot_survival_curve_health_combine(combined_experiments,...
        sep_exps_days_health,censored_wells_any_separated,legend_names_health,...
        max_days,name_of_exp,use_markers,use_title,font_size,csv_path);
end

out_folder = fullfile(csv_path,[name_of_exp '_lifespan.png']);

disp(out_folder);

% if ispc
%     cmd_command = ['explorer /select, ' out_folder];
%     system(cmd_command);
% else
%     out_folder = replace(out_folder,' ', '\ ');
%     terminal_command = ['open -R ' out_folder];
%     
%     system(terminal_command);
% end

end

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
    legend_names,max_days,name_of_exp,use_markers,use_title,colors_to_plot,font_size,csv_path)

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
xlabel('Days from adulthood','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

% save to a folder in output_figures
mkdir(fullfile(pwd,'output_figures'))

saveas(g,fullfile(pwd,'output_figures',[name_of_exp '_lifespan.png']))
saveas(g,fullfile(csv_path,[name_of_exp '_lifespan.png']));

hold off


end

function plot_survival_curve_health(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,colors_to_plot,font_size,csv_path)

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
xlabel('Days healthy from adulthood','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

saveas(g,fullfile(pwd,'output_figures',[name_of_exp '_healthspan.png']))
saveas(g,fullfile(csv_path,[name_of_exp '_healthspan.png']));

hold off


end




function [g] = plot_survival_curve_life_combine(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,font_size,csv_path)

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
        %
        %         ecdf_95 = std(ecdf_matrix,'omitnan')*2;
        %         ecdf_max = max(ecdf_matrix,[],'omitnan');
        %         ecdf_mean = mean(ecdf_matrix,'omitnan');
        %         ecdf_median = median(ecdf_matrix,'omitnan');
        
        stairs(x,this_survival_curve,...
            'LineStyle','-','LineWidth',5,...
            'Color','k')
        
        %         neg_err = this_survival_curve-ecdf_95(x)';
        %         neg_err(neg_err<0) = 0;
        %
        %         pos_err = this_survival_curve+ecdf_95(x)';
        %         for j = 1:length(pos_err)
        %             if pos_err(j) > ecdf_max(x(j))
        %                 pos_err(j) = ecdf_max(x(j));
        %             end
        %         end
        
        %         stairs(x,neg_err,...
        %             'LineStyle','--','LineWidth',2,...
        %             'Color','k')
        %         stairs(x,pos_err,...
        %             'LineStyle','--','LineWidth',2,...
        %             'Color','k')
        %         stairs(x,ecdf_mean(x),...
        %             'LineStyle','--','LineWidth',3,...
        %             'Color','b')
        %         stairs(x,ecdf_median(x),...
        %             'LineStyle','--','LineWidth',3,...
        %             'Color','r')
        %         stairs(x,flo,...
        %             'LineStyle','--','LineWidth',3,...
        %             'Color','b')
        %         stairs(x,fup,...
        %             'LineStyle','--','LineWidth',3,...
        %             'Color','r')
        
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
xlabel('Days from adulthood','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

% save to a folder in output_figures
mkdir(fullfile(pwd,'output_figures'))

saveas(g,char(fullfile(pwd,'output_figures',[name_of_exp '_lifespan.png'])));
saveas(g,fullfile(csv_path,[name_of_exp '_lifespan.png']));

hold off

end

function plot_survival_curve_health_combine(conditions,days_survived,censor,...
    legend_names,max_days,name_of_exp,use_markers,use_title,font_size,csv_path)

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
xlabel('Days healthy from adulthood','FontSize',20,'FontWeight','bold');
xlim([0,max_days+2])
xticks([0:5:max_days+2])
legend(legend_names, 'interpreter','none','FontSize',font_size);

saveas(g,char(fullfile(pwd,'output_figures',[name_of_exp '_healthspan.png'])));
saveas(g,fullfile(csv_path,[name_of_exp '_healthspan.png']));

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
    1,1,0;... % yellow
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


