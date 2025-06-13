import os

# Chemin du fichier
file_path = 'venture_link_project/settings/base.py'

# Lire le contenu du fichier
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Corriger la syntaxe
corrected_content = content.replace("'celery'\n    \n    # Custom apps", "'celery',\n    \n    # Custom apps")

# Écrire le contenu corrigé
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(corrected_content)

print("Correction effectuée avec succès !") 