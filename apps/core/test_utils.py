"""
Utilitaires pour les tests dans VentureLink.
"""
from unittest.mock import patch
from django.test.runner import DiscoverRunner


class NoFirebaseTestRunner(DiscoverRunner):
    """
    Test runner personnalisé qui désactive l'initialisation de Firebase.
    """
    
    def setup_test_environment(self, **kwargs):
        """
        Configure l'environnement de test.
        Applique un patch sur l'initialisation de Firebase.
        """
        # Patch firebase.initialize_firebase pour qu'il renvoie toujours True sans réelle initialisation
        self.firebase_patcher = patch('apps.core.firebase.initialize_firebase', return_value=True)
        self.firebase_patcher.start()
        
        # Appeler la méthode parente
        super().setup_test_environment(**kwargs)
    
    def teardown_test_environment(self, **kwargs):
        """
        Nettoie l'environnement de test.
        Arrête le patch sur l'initialisation de Firebase.
        """
        # Arrêter le patch
        self.firebase_patcher.stop()
        
        # Appeler la méthode parente
        super().teardown_test_environment(**kwargs) 