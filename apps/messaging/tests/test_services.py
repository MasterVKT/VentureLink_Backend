"""
Tests pour les services de l'application messaging.
"""
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.messaging.models import Conversation, Message, MessageAttachment, MessageRead
from apps.messaging.services.conversation_service import ConversationService
from apps.messaging.services.message_service import MessageService
from apps.core.exceptions import ResourceNotFoundError, ValidationError, PermissionDeniedError


class ConversationServiceTest(TestCase):
    """Tests pour le service ConversationService."""

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
        
        # Créer une catégorie et un projet pour les tests de conversation de projet
        self.category = ProjectCategory.objects.create(
            name_fr='Technologie',
            name_en='Technology'
        )
        
        self.project = Project.objects.create(
            creator=self.user1,
            title='Projet de test',
            short_description='Description courte du projet',
            full_description='Description longue du projet qui contient suffisamment de caractères.',
            category=self.category,
            is_draft=False
        )

    def test_get_user_conversations(self):
        """Test la récupération des conversations d'un utilisateur."""
        # Créer plusieurs conversations
        conv1 = ConversationService.create_direct_conversation(
            creator=self.user1,
            other_user=self.user2
        )
        
        conv2 = ConversationService.create_group_conversation(
            creator=self.user1,
            title="Groupe test",
            participants=[self.user2, self.user3]
        )
        
        conv3 = ConversationService.create_direct_conversation(
            creator=self.user2,
            other_user=self.user3
        )
        
        # Tester avec l'utilisateur 1
        conversations = ConversationService.get_user_conversations(user=self.user1)
        self.assertEqual(conversations.count(), 2)
        self.assertIn(conv1, conversations)
        self.assertIn(conv2, conversations)
        self.assertNotIn(conv3, conversations)
        
        # Tester avec l'utilisateur 2
        conversations = ConversationService.get_user_conversations(user=self.user2)
        self.assertEqual(conversations.count(), 3)
        self.assertIn(conv1, conversations)
        self.assertIn(conv2, conversations)
        self.assertIn(conv3, conversations)

    def test_get_conversation_by_id(self):
        """Test la récupération d'une conversation par ID."""
        # Créer une conversation
        conversation = ConversationService.create_direct_conversation(
            creator=self.user1,
            other_user=self.user2
        )
        
        # Récupérer la conversation en tant que participant
        retrieved_conv = ConversationService.get_conversation_by_id(
            conversation_id=conversation.id,
            user=self.user1
        )
        self.assertEqual(retrieved_conv, conversation)
        
        # Non-participant ne peut pas récupérer la conversation
        with self.assertRaises(ResourceNotFoundError):
            ConversationService.get_conversation_by_id(
                conversation_id=conversation.id,
                user=self.user3
            )

    def test_create_direct_conversation(self):
        """Test la création d'une conversation directe."""
        # Créer une conversation directe
        conversation = ConversationService.create_direct_conversation(
            creator=self.user1,
            other_user=self.user2
        )
        
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_DIRECT)
        self.assertIsNone(conversation.title)
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())
        
        # Vérifier que les participations sont créées
        self.assertTrue(conversation.conversation_participants.filter(user=self.user1).exists())
        self.assertTrue(conversation.conversation_participants.filter(user=self.user2).exists())
        
        # Tester la création d'une conversation qui existe déjà
        existing_conv = ConversationService.create_direct_conversation(
            creator=self.user1,
            other_user=self.user2
        )
        self.assertEqual(existing_conv, conversation)  # Devrait retourner la conversation existante

    def test_create_group_conversation(self):
        """Test la création d'une conversation de groupe."""
        # Créer une conversation de groupe
        conversation = ConversationService.create_group_conversation(
            creator=self.user1,
            title="Groupe de test",
            participants=[self.user2, self.user3]
        )
        
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_GROUP)
        self.assertEqual(conversation.title, "Groupe de test")
        self.assertEqual(conversation.participants.count(), 3)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())
        self.assertIn(self.user3, conversation.participants.all())
        
        # Vérifier que le créateur est administrateur
        creator_participation = conversation.conversation_participants.get(user=self.user1)
        self.assertTrue(creator_participation.is_admin)
        
        # Vérifier que les autres ne sont pas administrateurs
        other_participation = conversation.conversation_participants.get(user=self.user2)
        self.assertFalse(other_participation.is_admin)

    def test_create_project_conversation(self):
        """Test la création d'une conversation de projet."""
        # Créer une conversation de projet
        conversation = ConversationService.create_project_conversation(
            creator=self.user1,
            project=self.project,
            participants=[self.user2]
        )
        
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_PROJECT)
        self.assertEqual(conversation.project, self.project)
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())

    def test_add_participants(self):
        """Test l'ajout de participants à une conversation."""
        # Créer une conversation
        conversation = ConversationService.create_group_conversation(
            creator=self.user1,
            title="Groupe initial",
            participants=[self.user2]
        )
        
        # Ajouter un participant
        ConversationService.add_participants(
            conversation_id=conversation.id,
            user=self.user1,
            participants=[self.user3]
        )
        
        # Vérifier que le participant a été ajouté
        conversation.refresh_from_db()
        self.assertEqual(conversation.participants.count(), 3)
        self.assertIn(self.user3, conversation.participants.all())
        
        # Tester qu'un non-admin ne peut pas ajouter de participants
        other_user = User.objects.create_user(
            email='other@venturelink.com',
            password='testpassword'
        )
        
        with self.assertRaises(PermissionDeniedError):
            ConversationService.add_participants(
                conversation_id=conversation.id,
                user=self.user2,  # Non-admin
                participants=[other_user]
            )

    def test_remove_participant(self):
        """Test la suppression d'un participant d'une conversation."""
        # Créer une conversation
        conversation = ConversationService.create_group_conversation(
            creator=self.user1,
            title="Groupe test",
            participants=[self.user2, self.user3]
        )
        
        # Supprimer un participant
        ConversationService.remove_participant(
            conversation_id=conversation.id,
            user=self.user1,  # Admin
            participant_id=self.user3.id
        )
        
        # Vérifier que le participant a été supprimé
        conversation.refresh_from_db()
        self.assertEqual(conversation.participants.count(), 2)
        self.assertNotIn(self.user3, conversation.participants.all())
        
        # Tester qu'un non-admin ne peut pas supprimer de participants
        with self.assertRaises(PermissionDeniedError):
            ConversationService.remove_participant(
                conversation_id=conversation.id,
                user=self.user2,  # Non-admin
                participant_id=self.user1.id
            )

    def test_leave_conversation(self):
        """Test qu'un utilisateur peut quitter une conversation."""
        # Créer une conversation
        conversation = ConversationService.create_group_conversation(
            creator=self.user1,
            title="Groupe test",
            participants=[self.user2, self.user3]
        )
        
        # Quitter la conversation
        ConversationService.leave_conversation(
            conversation_id=conversation.id,
            user=self.user2
        )
        
        # Vérifier que l'utilisateur n'est plus dans la conversation
        conversation.refresh_from_db()
        self.assertEqual(conversation.participants.count(), 2)
        self.assertNotIn(self.user2, conversation.participants.all())

    def test_archive_conversation(self):
        """Test l'archivage d'une conversation."""
        # Créer une conversation
        conversation = ConversationService.create_direct_conversation(
            creator=self.user1,
            other_user=self.user2
        )
        
        # Archiver la conversation
        ConversationService.archive_conversation(
            conversation_id=conversation.id,
            user=self.user1
        )
        
        # Vérifier que la conversation est archivée pour l'utilisateur
        participation = conversation.conversation_participants.get(user=self.user1)
        self.assertEqual(participation.status, Conversation.STATUS_ARCHIVED)
        
        # Vérifier que la conversation n'est pas archivée pour l'autre utilisateur
        participation = conversation.conversation_participants.get(user=self.user2)
        self.assertEqual(participation.status, Conversation.STATUS_ACTIVE)


class MessageServiceTest(TestCase):
    """Tests pour le service MessageService."""

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
            title="Conversation de test",
            conversation_type=Conversation.TYPE_GROUP
        )
        self.conversation.participants.add(self.user1, self.user2)

    def test_get_conversation_messages(self):
        """Test la récupération des messages d'une conversation."""
        # Créer des messages
        message1 = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message 1",
            message_type=Message.TYPE_TEXT
        )
        
        message2 = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user2,
            content="Message 2",
            message_type=Message.TYPE_TEXT
        )
        
        # Récupérer les messages
        messages = MessageService.get_conversation_messages(
            conversation_id=self.conversation.id,
            user=self.user1
        )
        
        self.assertEqual(len(messages), 2)
        self.assertIn(message1, messages)
        self.assertIn(message2, messages)
        
        # Tester qu'un non-participant ne peut pas récupérer les messages
        with self.assertRaises(ResourceNotFoundError):
            MessageService.get_conversation_messages(
                conversation_id=self.conversation.id,
                user=self.user3
            )

    def test_get_message_by_id(self):
        """Test la récupération d'un message par ID."""
        # Créer un message
        message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message de test",
            message_type=Message.TYPE_TEXT
        )
        
        # Récupérer le message
        retrieved_message = MessageService.get_message_by_id(
            message_id=message.id,
            conversation_id=self.conversation.id,
            user=self.user1
        )
        
        self.assertEqual(retrieved_message, message)
        
        # Tester qu'un non-participant ne peut pas récupérer le message
        with self.assertRaises(ResourceNotFoundError):
            MessageService.get_message_by_id(
                message_id=message.id,
                conversation_id=self.conversation.id,
                user=self.user3
            )

    def test_create_message(self):
        """Test la création d'un message."""
        # Créer un message
        message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message de test",
            message_type=Message.TYPE_TEXT
        )
        
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.content, "Message de test")
        self.assertEqual(message.message_type, Message.TYPE_TEXT)
        self.assertEqual(message.status, Message.STATUS_SENT)
        
        # Vérifier que la date du dernier message de la conversation est mise à jour
        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation.last_message_at)

    def test_create_reply(self):
        """Test la création d'une réponse à un message."""
        # Créer un message
        original_message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message original",
            message_type=Message.TYPE_TEXT
        )
        
        # Créer une réponse
        reply = MessageService.create_reply(
            conversation_id=self.conversation.id,
            user=self.user2,
            parent_message_id=original_message.id,
            content="Réponse au message",
            message_type=Message.TYPE_TEXT
        )
        
        self.assertEqual(reply.conversation, self.conversation)
        self.assertEqual(reply.sender, self.user2)
        self.assertEqual(reply.content, "Réponse au message")
        self.assertEqual(reply.parent, original_message)

    def test_mark_message_as_read(self):
        """Test le marquage d'un message comme lu."""
        # Créer un message
        message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message à lire",
            message_type=Message.TYPE_TEXT
        )
        
        # Marquer le message comme lu
        MessageService.mark_message_as_read(
            message_id=message.id,
            conversation_id=self.conversation.id,
            user=self.user2
        )
        
        # Vérifier qu'un accusé de lecture a été créé
        self.assertTrue(MessageRead.objects.filter(
            message=message,
            user=self.user2
        ).exists())

    def test_delete_message(self):
        """Test la suppression d'un message."""
        # Créer un message
        message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Message à supprimer",
            message_type=Message.TYPE_TEXT
        )
        
        # Supprimer le message
        MessageService.delete_message(
            message_id=message.id,
            conversation_id=self.conversation.id,
            user=self.user1
        )
        
        # Vérifier que le message est marqué comme supprimé
        message.refresh_from_db()
        self.assertEqual(message.status, Message.STATUS_DELETED)
        
        # Tester qu'un utilisateur ne peut pas supprimer le message d'un autre
        message = MessageService.create_message(
            conversation_id=self.conversation.id,
            user=self.user1,
            content="Autre message",
            message_type=Message.TYPE_TEXT
        )
        
        with self.assertRaises(PermissionDeniedError):
            MessageService.delete_message(
                message_id=message.id,
                conversation_id=self.conversation.id,
                user=self.user2
            ) 