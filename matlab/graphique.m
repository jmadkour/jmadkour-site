% Richesse et chomage par region
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

pib_hab = [38 21 52 16 27 45 19 30];
chomage = [9.2 12.4 7.8 15.1 10.6 8.3 13.9 11.2];

plot(pib_hab, chomage, 'o', 'MarkerSize', 8)
xlabel('PIB par habitant (milliers de DH)')
ylabel('Taux de chomage (%)')
title('Richesse et chomage par region')
grid on
