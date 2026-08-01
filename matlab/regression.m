% Une regression par moindres carres
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

pib_hab = [38 21 52 16 27 45 19 30]';        % en milliers de dirhams
chomage = [9.2 12.4 7.8 15.1 10.6 8.3 13.9 11.2]';

X = [ones(8,1) pib_hab];      % colonne de 1 pour la constante
beta = X \ chomage
