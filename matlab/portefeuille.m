% Rendement et risque d'un portefeuille
% Cours Outils - MATLAB / Octave, chapitre 1
% jmadkour.org

w = [0.5; 0.3; 0.2];              % poids du portefeuille
r = [0.08; 0.12; 0.05];           % rendements esperes

S = [0.040  0.012  0.005;         % matrice de covariances
     0.012  0.090  0.008;
     0.005  0.008  0.020];

rendement = w' * r
variance  = w' * S * w
risque    = sqrt(variance)
