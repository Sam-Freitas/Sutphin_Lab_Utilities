clear all
close all

a2 = imread('a2.png');
well_distaces = readtable('well_distances.csv','VariableNamingRule','preserve');
large_table = readtable('Compiled_table.csv','VariableNamingRule','preserve');

column_dosage = string(large_table.Dosage);
column_strain = string(large_table.Strain);

control_n2_row_idx = logical((column_dosage == 'Control').*(column_strain == 'n2'));

controls_table = large_table(control_n2_row_idx,:);

lifespans = controls_table.("Last day of observation");
healthspans = controls_table.("Last day of health");
well_loc = controls_table.("Well Location");

well_dist_from_center_norm = zeros(size(well_loc));
well_dist_to_edge_norm = zeros(size(well_loc));
for i = 1:length(well_loc)
    
    this_well = well_loc(i);
    
    well_dist_from_center_norm(i) = table2array(well_distaces(this_well,2));
    well_dist_to_edge_norm(i) = table2array(well_distaces(this_well,3));
    
end

T = cell2table(num2cell(well_dist_from_center_norm));
T.Properties.VariableNames = ["Well Distance from center"];

controls_table = [controls_table T];

[R_center,P_center] = corrcoef(controls_table.("Last day of observation"),well_dist_from_center_norm);
[R_edge,P_edge] = corrcoef(controls_table.("Last day of observation"),well_dist_to_edge_norm);








