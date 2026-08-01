% Extraire, mesurer, decrire
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

chomage = [9.2 12.4 7.8 15.1 10.6 8.3 13.9 11.2];

mean(chomage)              % moyenne
std(chomage)               % ecart-type
max(chomage)               % maximum
sum(chomage > 12)          % combien depassent 12 %
chomage(chomage > 12)      % lesquelles
