- Pour implémenter ce projet, tu suivra le plan de développement mentionné dans le fichier "Plan_de_Developpement_Backend_VentureLink.txt";
- Avant chacune de tes réponses ou actions, vérifie qu'elle suit l'ordre du plan de développement et qu'elle est conforme aux spécifications du projet contenues dans les fichiers:"Architecture Backend VentureLink.txt", "Contrats_API_RESTFul_VentureLink.txt", "Conventions_et_Standards_VentureLink.txt", "Documentation_des_Services_Firebase_VentureLink.txt", "Flux_Intégration_VentureLink.txt", "Format_Données_Echangees_VentureLink.txt" tous contenus dans le dossier "docs" à la racine du projet;; 

- Avant chacune de tes réponses ou actions, vérifie si tu disposes de toutes les informations qui te permettront de donner la réponse ou action attendue et une réponse ou action pertinente et efficace. Si tel n'est pas le cas, pose moi les questions necessaires;

- Après avoir donné une réponse ou effectué une action, fais une synthèse de ce qui a déjà été fait et ce qui reste à faire.

- Pense à implémenter la possibilité d'utiliser plusieurs devises monétaires (au choix de l'utilisateur) et implémente la fonctionnalité permettant la conversion automatique des valeurs monétaires à l'affichage en fonction des préférences ou de la devise de l'utilisateur;

- Le fichier "google-services.json" est celui qui a été utilisé dans le frontend pour la configuration firebase.

- Je pense qu'il serait mieux pour toi d'executer tes commandes dans le "Command prompt" au lieu de Powershell (à moins que tu ne penses que PowerShell est mieux; tu décideras toi même)

- Avant d'installer des paquets avec pip, rassure toi de le faire dans l'environnement virtuel python lié au projet. Si tu utilises powershell, pour activer l'environnement virtuel tu devra entrer ces commandes dans l'ordre:
1) Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
2)..\Scripts\Activate

- Pour gérer les paiements, tu utiliseras l'API de My-CoolPay dont la description est donnée dans le fichier "My-CoolPay API Docs.pdf" situé dans le dossier docs à la racine de ce projet. On se servira du bac à sable pour le développement avant d'utiliser la clé d'API réelle pour la production,  donc structure le code de façon à ce que cette transition soit la plus facile et simple possible.

- Cette application est destinée à être internationnalisée, donc il faut penser à ça dans le code si besoin est.

-  Si les tâches que tu effectues doivent entraîner des modifications dans le frontend pour que l'application fonctionne correctement, dis le moi en me présentant de façon détaillée, précise et structurée ce qu'il faudra faire; cependant le meilleur des cas est que la résolution de problèmes ici n'entraîne pas ou peu de modifications du backend