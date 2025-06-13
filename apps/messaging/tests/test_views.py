"""
Tests pour les vues de l'application messaging.
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User
from apps.messaging.models import Conversation, Message, MessageAttachment


class ConversationViewSetTest(TestCase):
    """Tests pour les endpoints de conversation."""

    def setUp(self):
        # Créer des utilisateurs pour les tests
        self.user1 = User.objects.create_user(
            email='user1@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='Two'
        )
        
        self.user3 = User.objects.create_user(
            email='user3@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='Three'
        )
        
        # Créer une conversation directe entre user1 et user2
        self.direct_conversation = Conversation.objects.create(
            title=None,
            conversation_type=Conversation.TYPE_DIRECT
        )
        self.direct_conversation.participants.add(self.user1, self.user2)
        
        # Créer une conversation de groupe
        self.group_conversation = Conversation.objects.create(
            title="Groupe de test",
            conversation_type=Conversation.TYPE_GROUP
        )
        self.group_conversation.participants.add(self.user1, self.user2, self.user3)
        
        # Ajouter quelques messages
        self.message1 = Message.objects.create(
            conversation=self.direct_conversation,
            sender=self.user1,
            content="Message de test 1",
            message_type=Message.TYPE_TEXT
        )
        
        self.message2 = Message.objects.create(
            conversation=self.direct_conversation,
            sender=self.user2,
            content="Message de test 2",
            message_type=Message.TYPE_TEXT
        )
        
        # Initialiser le client API
        self.client = APIClient()

    def test_list_conversations_anonymous(self):
        """Test: un utilisateur non authentifié ne peut pas voir les conversations."""
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_conversations_authenticated(self):
        """Test: un utilisateur authentifié peut voir ses conversations."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # user1 participe à 2 conversations

    def test_retrieve_conversation(self):
        """Test: un participant peut consulter les détails d'une conversation."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-detail', kwargs={'pk': self.direct_conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.direct_conversation.id))
        self.assertEqual(response.data['conversation_type'], Conversation.TYPE_DIRECT)
        
        # Vérifier que les participants sont inclus
        self.assertEqual(len(response.data['participants']), 2)

    def test_retrieve_conversation_non_participant(self):
        """Test: un non-participant ne peut pas accéder aux détails d'une conversation."""
        self.client.force_authenticate(user=self.user3)
        url = reverse('conversation-detail', kwargs={'pk': self.direct_conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_direct_conversation(self):
        """Test: créer une nouvelle conversation directe."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-list')
        
        data = {
            'conversation_type': Conversation.TYPE_DIRECT,
            'participants': [str(self.user3.id)],  # Nouvelle conversation avec user3
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que la conversation a été créée
        new_conversation_id = response.data['id']
        conversation = Conversation.objects.get(id=new_conversation_id)
        
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_DIRECT)
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user3, conversation.participants.all())

    def test_create_group_conversation(self):
        """Test: créer une nouvelle conversation de groupe."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-list')
        
        data = {
            'title': 'Nouveau groupe',
            'conversation_type': Conversation.TYPE_GROUP,
            'participants': [str(self.user2.id), str(self.user3.id)],
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que la conversation a été créée
        new_conversation_id = response.data['id']
        conversation = Conversation.objects.get(id=new_conversation_id)
        
        self.assertEqual(conversation.title, 'Nouveau groupe')
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_GROUP)
        self.assertEqual(conversation.participants.count(), 3)

    def test_archive_conversation(self):
        """Test: archiver une conversation."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-archive', kwargs={'pk': self.direct_conversation.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que la conversation est archivée pour l'utilisateur
        participation = self.user1.conversation_participations.get(
            conversation=self.direct_conversation
        )
        self.assertEqual(participation.status, Conversation.STATUS_ARCHIVED)


class MessageViewSetTest(TestCase):
    """Tests pour les endpoints de message."""

    def setUp(self):
        # Créer des utilisateurs pour les tests
        self.user1 = User.objects.create_user(
            email='user1@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='Two'
        )
        
        self.user3 = User.objects.create_user(
            email='user3@venturelink.com',
            password='testpassword',
            first_name='User',
            last_name='Three'
        )
        
        # Créer une conversation
        self.conversation = Conversation.objects.create(
            title=None,
            conversation_type=Conversation.TYPE_DIRECT
        )
        self.conversation.participants.add(self.user1, self.user2)
        
        # Ajouter quelques messages
        self.message1 = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Message de test 1",
            message_type=Message.TYPE_TEXT
        )
        
        self.message2 = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content="Message de test 2",
            message_type=Message.TYPE_TEXT
        )
        
        # Initialiser le client API
        self.client = APIClient()

    def test_list_messages_anonymous(self):
        """Test: un utilisateur non authentifié ne peut pas voir les messages."""
        url = reverse('conversation-message-list', kwargs={'conversation_pk': self.conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_messages_participant(self):
        """Test: un participant peut voir les messages d'une conversation."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-message-list', kwargs={'conversation_pk': self.conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 2 messages dans la conversation

    def test_list_messages_non_participant(self):
        """Test: un non-participant ne peut pas voir les messages."""
        self.client.force_authenticate(user=self.user3)
        url = reverse('conversation-message-list', kwargs={'conversation_pk': self.conversation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_message(self):
        """Test: créer un nouveau message dans une conversation."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-message-list', kwargs={'conversation_pk': self.conversation.id})
        
        data = {
            'content': 'Nouveau message de test',
            'message_type': Message.TYPE_TEXT
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Vérifier que le message a été créé
        self.assertTrue(Message.objects.filter(
            conversation=self.conversation,
            sender=self.user1,
            content='Nouveau message de test'
        ).exists())

    def test_non_participant_cannot_create_message(self):
        """Test: un non-participant ne peut pas créer de message."""
        self.client.force_authenticate(user=self.user3)
        url = reverse('conversation-message-list', kwargs={'conversation_pk': self.conversation.id})
        
        data = {
            'content': 'Message indésirable',
            'message_type': Message.TYPE_TEXT
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Vérifier qu'aucun message n'a été créé
        self.assertFalse(Message.objects.filter(content='Message indésirable').exists())

    def test_mark_message_as_read(self):
        """Test: marquer un message comme lu."""
        self.client.force_authenticate(user=self.user2)
        url = reverse('conversation-message-read', kwargs={
            'conversation_pk': self.conversation.id,
            'pk': self.message1.id
        })
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le message est marqué comme lu
        self.assertTrue(self.message1.read_receipts.filter(user=self.user2).exists())

    def test_delete_message(self):
        """Test: supprimer un message."""
        self.client.force_authenticate(user=self.user1)
        url = reverse('conversation-message-detail', kwargs={
            'conversation_pk': self.conversation.id,
            'pk': self.message1.id
        })
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier que le message a été marqué comme supprimé (mais pas réellement supprimé)
        self.message1.refresh_from_db()
        self.assertEqual(self.message1.status, Message.STATUS_DELETED)

    def test_other_user_cannot_delete_message(self):
        """Test: un utilisateur ne peut pas supprimer le message d'un autre."""
        self.client.force_authenticate(user=self.user2)
        url = reverse('conversation-message-detail', kwargs={
            'conversation_pk': self.conversation.id,
            'pk': self.message1.id
        })
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Vérifier que le message n'a pas été supprimé
        self.message1.refresh_from_db()
        self.assertNotEqual(self.message1.status, Message.STATUS_DELETED) 