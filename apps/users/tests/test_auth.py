"""
Tests pour l'authentification des utilisateurs.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class FirebaseAuthenticationTests(TestCase):
    """Tests pour l'authentification Firebase."""
    
    def setUp(self):
        self.client = APIClient()
        self.firebase_auth_url = reverse('firebase_auth')
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        }
        
    @patch('apps.core.utils.firebase.verify_firebase_token')
    def test_firebase_auth_success(self, mock_verify_token):
        """Test d'authentification Firebase réussie."""
        # Configurer le mock pour verify_firebase_token
        mock_verify_token.return_value = {
            'uid': 'firebase-uid-123',
            'email': self.user_data['email'],
            'name': f"{self.user_data['first_name']} {self.user_data['last_name']}",
            'picture': 'https://example.com/photo.jpg',
            'email_verified': True,
            'provider_id': 'password',
        }
        
        # Requête d'authentification
        response = self.client.post(
            self.firebase_auth_url,
            {'id_token': 'fake-firebase-token'},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('is_new_user', response.data)
        
        # Vérifier que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())
        
    @patch('apps.core.utils.firebase.verify_firebase_token')
    def test_firebase_auth_existing_user(self, mock_verify_token):
        """Test d'authentification Firebase avec un utilisateur existant."""
        # Créer un utilisateur
        user = User.objects.create_user(
            email=self.user_data['email'],
            password='testpassword',
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )
        
        # Configurer le mock pour verify_firebase_token
        mock_verify_token.return_value = {
            'uid': 'firebase-uid-123',
            'email': self.user_data['email'],
            'name': f"{self.user_data['first_name']} {self.user_data['last_name']}",
            'email_verified': True,
        }
        
        # Requête d'authentification
        response = self.client.post(
            self.firebase_auth_url,
            {'id_token': 'fake-firebase-token'},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['is_new_user'], False)
        
    @patch('apps.core.utils.firebase.verify_firebase_token')
    def test_firebase_auth_invalid_token(self, mock_verify_token):
        """Test d'authentification Firebase avec un token invalide."""
        # Configurer le mock pour verify_firebase_token pour lever une exception
        mock_verify_token.side_effect = ValueError("Token Firebase invalide")
        
        # Requête d'authentification
        response = self.client.post(
            self.firebase_auth_url,
            {'id_token': 'invalid-token'},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
    def test_firebase_auth_missing_token(self):
        """Test d'authentification Firebase sans token."""
        # Requête d'authentification sans token
        response = self.client.post(
            self.firebase_auth_url,
            {},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class TokenRefreshTests(TestCase):
    """Tests pour le rafraîchissement des tokens."""
    
    def setUp(self):
        self.client = APIClient()
        self.token_refresh_url = reverse('token_refresh')
        self.custom_token_refresh_url = reverse('custom_token_refresh')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
    def get_tokens(self):
        """Obtient un jeu de tokens pour l'utilisateur de test."""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
    def test_token_refresh_success(self):
        """Test de rafraîchissement de token réussi."""
        tokens = self.get_tokens()
        
        # Requête de rafraîchissement
        response = self.client.post(
            self.token_refresh_url,
            {'refresh': tokens['refresh']},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
    def test_custom_token_refresh_success(self):
        """Test de rafraîchissement de token personnalisé réussi."""
        tokens = self.get_tokens()
        
        # Requête de rafraîchissement
        response = self.client.post(
            self.custom_token_refresh_url,
            {'refresh': tokens['refresh']},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_token_refresh_invalid_token(self):
        """Test de rafraîchissement avec un token invalide."""
        # Requête de rafraîchissement avec un token invalide
        response = self.client.post(
            self.custom_token_refresh_url,
            {'refresh': 'invalid-token'},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
    def test_token_refresh_missing_token(self):
        """Test de rafraîchissement sans token."""
        # Requête de rafraîchissement sans token
        response = self.client.post(
            self.custom_token_refresh_url,
            {},
            format='json'
        )
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data) 