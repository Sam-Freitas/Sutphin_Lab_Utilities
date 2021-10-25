
data_path = uigetdir(pwd,'Select the folder containing the individual data folders');

data_dir = dir(data_path);

dir_flags = [data_dir.isdir];

data_dir = data_dir(dir_flags);

data_dir(ismember( {data_dir.name},{'..','.','Old_data','Sutphin_Lab_Utilities','Compiled_table'})) = [];

for i = 1:length(data_dir)
    
    disp(data_dir(i).name)
    
    temp_dir_step = dir(fullfile(data_dir(i).folder,data_dir(i).name));
    
    dir_step_names = {temp_dir_step.name};
    
    TF = zeros(1,length(dir_step_names));
    
    for j = 1:length(dir_step_names)
        
        TF(j) = contains(dir_step_names{j},'.csv');
        
    end
    
    csv_idx = nonzeros([1:length(TF)].*TF);
    
    if ~isempty(csv_idx)
        
        if isequal(length(csv_idx),1)
            temp_table = readtable(fullfile(temp_dir_step(csv_idx).folder,...
                temp_dir_step(csv_idx).name),...
                'VariableNamingRule','preserve' );
            
            this_temp_exp_name = data_dir(i).name;
            
            exp_column = repmat({this_temp_exp_name},size(temp_table.("Worm number")));
            
            temp_table.("Experiment Name") = exp_column;
            
            try
                temp_table.Strain = lower(temp_table.Strain);
                
                dosages = temp_table.Dosage;
                
                for j = 1:length(dosages)
                    
                    split_dosage = strsplit(dosages{j});
                    
                    if length(split_dosage) > 1
                        for k = 1:length(split_dosage)
                            split_dosage{k}(1) = upper(split_dosage{k}(1));
                        end
                        
                    else
                        split_dosage{1}(1) = upper(split_dosage{1}(1));
                    end
                    
                    dosages{j} = strjoin(split_dosage);
                    
                end
                
                temp_table.Dosage = dosages;
                
            catch
                temp_table.Dosage = temp_table.("Group ID");
                temp_table.Strain = repmat({'Not Recorded'},size(temp_table.Dosage));
                
                temp_table_vars = temp_table.Properties.VariableNames;
                
                not_needed_idx = contains(temp_table_vars,'ID');     
                
                temp_table = temp_table(:,~not_needed_idx);
                
            end
            
        else
            temp_table = [];
        end
    end
    
    if isequal(i,1)
        massive_table = temp_table(:,[1:13,end]);
        
        massive_table = [massive_table(:,1) massive_table(:,end) massive_table(:,2:13)];
        
    else
        try
            massive_table = [massive_table;temp_table(:,[1:13,end])];
        catch
            disp(['            skipping ' data_dir(i).name]);
        end
    end
    
end

writetable(massive_table,fullfile(data_path,'Compiled_table.csv'))
writetable(massive_table,fullfile(pwd,'Compiled_table.csv'))

disp('output compiled data to:')
disp(fullfile(data_path,'Compiled_table.csv'));

