% Resoudre un equilibre de marche
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

% 2*P1 +   P2 = 100
%   P1 + 3*P2 = 150
A = [2 1; 1 3];
b = [100; 150];

P = A \ b
