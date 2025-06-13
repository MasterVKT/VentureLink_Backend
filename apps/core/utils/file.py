"""
Utilitaires pour la gestion des fichiers.
"""
import os
import uuid
from datetime import datetime


def get_file_path(instance, filename, directory):
    """
    Génère un chemin de fichier unique pour un fichier uploadé.
    
    Args:
        instance: L'instance du modèle auquel le fichier est attaché
        filename (str): Le nom original du fichier
        directory (str): Le sous-répertoire où le fichier sera stocké
    
    Returns:
        str: Le chemin du fichier avec un nom unique
    """
    # Extraire l'extension du fichier original
    ext = filename.split('.')[-1] if '.' in filename else ''
    
    # Créer un nouveau nom de fichier basé sur UUID et timestamp
    new_filename = f"{uuid.uuid4().hex}_{int(datetime.now().timestamp())}"
    if ext:
        new_filename = f"{new_filename}.{ext}"
    
    # Construire le chemin complet
    return os.path.join(directory, new_filename) 