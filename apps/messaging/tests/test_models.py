"""
Tests for messaging models.
"""
from django.test import TestCase
from django.utils import timezone

from apps.users.models import User
from apps.projects.models import Project, ProjectCategory
from apps.messaging.models import (
    Conversation, ConversationParticipant, 
    Message, MessageAttachment, MessageRead
)


class ConversationModelTests(TestCase):
    """
    Tests for the Conversation model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        # Create users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='password123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='password123',
            first_name='User',
            last_name='Two'
        )
        
        # Create a project category
        self.category = ProjectCategory.objects.create(name_fr='Tech', name_en='Technology')
        
        # Create a project
        self.project = Project.objects.create(
            title='Test Project Description Example',
            short_description='A test project description that is long enough to pass validation rules',
            full_description='A comprehensive test project description that provides detailed information about the project goals, features, and implementation strategy.',
            creator=self.user1,
            category=self.category,
            funding_min=1000,
            funding_max=10000,
            stage='IDEA',
            status='ACTIVE'
        )
    
    def test_create_direct_conversation(self):
        """
        Test creating a direct conversation.
        """
        conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            status=Conversation.STATUS_ACTIVE
        )
        
        # Add participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1,
            is_admin=True
        )
        
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user2
        )
        
        # Verify
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_DIRECT)
        self.assertEqual(conversation.status, Conversation.STATUS_ACTIVE)
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())
    
    def test_create_project_conversation(self):
        """
        Test creating a project conversation.
        """
        conversation = Conversation.objects.create(
            title='Project Discussion',
            conversation_type=Conversation.TYPE_PROJECT,
            status=Conversation.STATUS_ACTIVE,
            project=self.project
        )
        
        # Add participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user1,
            is_admin=True
        )
        
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=self.user2
        )
        
        # Verify
        self.assertEqual(conversation.title, 'Project Discussion')
        self.assertEqual(conversation.conversation_type, Conversation.TYPE_PROJECT)
        self.assertEqual(conversation.status, Conversation.STATUS_ACTIVE)
        self.assertEqual(conversation.project, self.project)
        self.assertEqual(conversation.participants.count(), 2)
    
    def test_conversation_str_method(self):
        """
        Test the string representation of a conversation.
        """
        # Direct conversation
        direct_conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            status=Conversation.STATUS_ACTIVE
        )
        
        ConversationParticipant.objects.create(
            conversation=direct_conversation,
            user=self.user1
        )
        
        ConversationParticipant.objects.create(
            conversation=direct_conversation,
            user=self.user2
        )
        
        # Project conversation
        project_conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_PROJECT,
            status=Conversation.STATUS_ACTIVE,
            project=self.project
        )
        
        # Group conversation
        group_conversation = Conversation.objects.create(
            title='Group Chat',
            conversation_type=Conversation.TYPE_GROUP,
            status=Conversation.STATUS_ACTIVE
        )
        
        # Check string representations
        self.assertTrue('Discussion: User One & User Two' in str(direct_conversation) or 
                        'Discussion: User Two & User One' in str(direct_conversation))
        self.assertEqual(str(project_conversation), f"Projet: {self.project.title}")
        self.assertEqual(str(group_conversation), "Group Chat")


class MessageModelTests(TestCase):
    """
    Tests for the Message model.
    """
    
    def setUp(self):
        """
        Set up test data.
        """
        # Create users
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='password123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='password123',
            first_name='User',
            last_name='Two'
        )
        
        # Create a conversation
        self.conversation = Conversation.objects.create(
            conversation_type=Conversation.TYPE_DIRECT,
            status=Conversation.STATUS_ACTIVE
        )
        
        # Add participants
        ConversationParticipant.objects.create(
            conversation=self.conversation,
            user=self.user1,
            is_admin=True
        )
        
        ConversationParticipant.objects.create(
            conversation=self.conversation,
            user=self.user2
        )
    
    def test_create_message(self):
        """
        Test creating a message.
        """
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            message_type=Message.TYPE_TEXT,
            content='Hello World!',
            status=Message.STATUS_SENT
        )
        
        # Verify
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.message_type, Message.TYPE_TEXT)
        self.assertEqual(message.content, 'Hello World!')
        self.assertEqual(message.status, Message.STATUS_SENT)
        self.assertFalse(message.is_system_message)
    
    def test_create_system_message(self):
        """
        Test creating a system message.
        """
        message = Message.objects.create(
            conversation=self.conversation,
            message_type=Message.TYPE_SYSTEM,
            content='User One added User Two to the conversation.',
            status=Message.STATUS_SENT,
            is_system_message=True
        )
        
        # Verify
        self.assertEqual(message.conversation, self.conversation)
        self.assertIsNone(message.sender)
        self.assertEqual(message.message_type, Message.TYPE_SYSTEM)
        self.assertEqual(message.content, 'User One added User Two to the conversation.')
        self.assertEqual(message.status, Message.STATUS_SENT)
        self.assertTrue(message.is_system_message)
    
    def test_message_replies(self):
        """
        Test message replies.
        """
        # Create an initial message
        initial_message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            message_type=Message.TYPE_TEXT,
            content='What do you think about our project?',
            status=Message.STATUS_SENT
        )
        
        # Create a reply
        reply = Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            message_type=Message.TYPE_TEXT,
            content='I think it looks promising!',
            status=Message.STATUS_SENT,
            parent=initial_message
        )
        
        # Verify
        self.assertEqual(reply.parent, initial_message)
        self.assertEqual(initial_message.replies.count(), 1)
        self.assertEqual(initial_message.replies.first(), reply)
    
    def test_message_read_receipts(self):
        """
        Test message read receipts.
        """
        # Create a message
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            message_type=Message.TYPE_TEXT,
            content='Can you read this?',
            status=Message.STATUS_SENT
        )
        
        # Create a read receipt
        read_time = timezone.now()
        read_receipt = MessageRead.objects.create(
            message=message,
            user=self.user2,
            read_at=read_time
        )
        
        # Verify
        self.assertEqual(read_receipt.message, message)
        self.assertEqual(read_receipt.user, self.user2)
        self.assertEqual(message.read_receipts.count(), 1)
        self.assertEqual(message.read_receipts.first(), read_receipt)
    
    def test_message_str_method(self):
        """
        Test the string representation of messages.
        """
        # Regular message
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            message_type=Message.TYPE_TEXT,
            content='This is a test message',
            status=Message.STATUS_SENT
        )
        
        # System message
        system_message = Message.objects.create(
            conversation=self.conversation,
            message_type=Message.TYPE_SYSTEM,
            content='System notification',
            status=Message.STATUS_SENT,
            is_system_message=True
        )
        
        # Check string representations
        self.assertEqual(str(message), f"User One: This is a test message...")
        self.assertEqual(str(system_message), f"[Système] System notification...")
    
    def test_message_attachment(self):
        """
        Test creating a message with an attachment.
        """
        # Create a message
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            message_type=Message.TYPE_FILE,
            content='Check out this document',
            status=Message.STATUS_SENT
        )
        
        # Create an attachment
        attachment = MessageAttachment.objects.create(
            message=message,
            file_name='document.pdf',
            file_size=1024 * 1024,  # 1MB
            file_type='application/pdf'
        )
        
        # Verify
        self.assertEqual(attachment.message, message)
        self.assertEqual(attachment.file_name, 'document.pdf')
        self.assertEqual(attachment.file_size, 1024 * 1024)
        self.assertEqual(attachment.file_type, 'application/pdf')
        self.assertEqual(message.attachments.count(), 1)
        self.assertEqual(message.attachments.first(), attachment)
        
        # Test human-readable file size
        self.assertEqual(attachment.get_file_size_display(), '1.0 Mo') 