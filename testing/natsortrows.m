% created by Samuel Freitas
% 9/20/21

% this is a simple program that is attemping to combine the
% two functions of naturally sorting a string or cell array
% and sorting by thw rows as by column

function [X_out,out_index] = natsortrows(X_in,sorting_columns)

% convert the resut to a string
X_str = string(X_in);

if sum(size(X_str) == 1)
    % if there is only one row or column just use the regular natsort 
    [X_out,out_index,~] = natsort(cellstr(X_str));
else
    
    % determine what columns are being sorted by
    if ~(exist('sorting_columns','var'))
        sorting_columns = 1:size(X_str,2);
    end
    
    % this converts the sorting columns into ascending values by natrually
    % sorting them
    
    column_idxs = zeros(size(X_str,1),length(sorting_columns));
    
    for i = 1:length(sorting_columns)
        % get the specific index
        this_col_idx = sorting_columns(i);
        % get the columns
        this_col = X_str(:,this_col_idx);
        % initalize the index
        this_out_idx = zeros(size(this_col));
        % naturally sort the uniuq values
        this_col_unique_sorted = string(natsort(cellstr(unique(this_col))));
        % for each unique value assign the out index an ascending number
        % sequence
        for j = 1:length(this_col_unique_sorted)
            unique_val_idx = (this_col==this_col_unique_sorted(j));
            this_out_idx(unique_val_idx) = j;
        end
        % input for the sortrows function
        column_idxs(:,i) = this_out_idx;
        
    end
    
    [~,out_index] = sortrows(column_idxs);
    
    X_out = X_in(out_index,:);
end

end
