% Modele entrees-sorties de Leontief
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

% part des consommations intermediaires
A = [0.2 0.3 0.1;
     0.1 0.2 0.3;
     0.2 0.1 0.2];

d = [100; 150; 80];    % demande finale

% production totale x telle que x = A*x + d
x = (eye(3) - A) \ d
