x=[randn(2,100) + 3, randn(2,100) - 3, randn(2,100)];
[centers distortion]=kml(single(x), 3, 3, 10);

scatter(x(1,:), x(2,:),12, 'Marker','+');
hold on;
scatter(centers(1,:), centers(2,:), 50, 'r','filled');