"""
Tests pour l'application investments.
"""
from unittest.mock import patch, MagicMock

# Mock Firebase pour les tests
firebase_patch = patch('apps.core.firebase.initialize_firebase')
mock_firebase = firebase_patch.start() 