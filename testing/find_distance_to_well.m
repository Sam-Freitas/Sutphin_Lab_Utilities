clear all 
close all force hidden


a2 = imread('a2.png');

unique_vals = double(unique(a2));
total_wells = length(unique_vals)-1;

centroids = zeros(total_wells,2);

for i = 1:total_wells
    disp(i)
    
    this_label = (a2==i);
    
    s = regionprops(this_label,'basic');
    
    centroids(i,:) = s.Centroid;
end

mean_centroid = mean(centroids,1);

distance_from_center = zeros(total_wells,1);

for i = 1:total_wells
    
    distance_from_center(i)  = sqrt(sum((mean_centroid - centroids(i,:)) .^ 2));

end

distance_from_center_norm = distance_from_center/max(distance_from_center);

plate = ones(14,22);
plate(2:13,2:21) = 0;
[Dist_to_edge_2d,idx] = bwdist(plate);

Dist_to_edge_2d = double(Dist_to_edge_2d(2:13,2:21));
Dist_to_edge_2d_norm = Dist_to_edge_2d/max(Dist_to_edge_2d(:));

Dist_to_edge_norm = Dist_to_edge_2d_norm(:);

data = num2cell([[1:total_wells]',distance_from_center_norm,Dist_to_edge_norm]);

T = cell2table(data);
T.Properties.VariableNames = ["Well Location","distance_from_center_norm","Distance_to_edge_norm"];

writetable(T,'well_distances.csv')






