# Documentation des APIs Messaging - VentureLink

## Vue d'ensemble

L'application **Messaging** de VentureLink fournit un système de messagerie complet permettant aux utilisateurs de communiquer via des conversations directes, des discussions de projet et des groupes. Le système supporte les messages texte, les pièces jointes, les accusés de lecture et les notifications en temps réel.

## Architecture du système

### Modèles de données

#### 1. Conversation
Modèle principal représentant une conversation entre utilisateurs.

**Types de conversation :**
- `DIRECT` : Message direct entre 2 utilisateurs
- `PROJECT` : Discussion liée à un projet spécifique
- `GROUP` : Conversation de groupe avec plusieurs participants

**Statuts :**
- `ACTIVE` : Conversation active
- `ARCHIVED` : Conversation archivée
- `DELETED` : Conversation supprimée

**Champs principaux :**
- `title` : Titre (obligatoire pour les groupes)
- `conversation_type` : Type de conversation
- `status` : Statut de la conversation
- `participants` : Utilisateurs participants (Many-to-Many)
- `project` : Projet associé (optionnel)
- `last_message_at` : Date du dernier message

#### 2. ConversationParticipant
Modèle de liaison pour les participants d'une conversation.

**Champs principaux :**
- `conversation` : Conversation associée
- `user` : Utilisateur participant
- `is_admin` : Statut administrateur
- `last_read_at` : Dernière lecture des messages
- `nickname` : Surnom personnalisé
- `status` : Statut du participant
- `muted_until` : Mise en sourdine jusqu'à

#### 3. Message
Modèle représentant un message dans une conversation.

**Types de message :**
- `TEXT` : Message texte
- `IMAGE` : Image
- `FILE` : Fichier
- `AUDIO` : Message audio
- `VIDEO` : Vidéo
- `LOCATION` : Localisation
- `SYSTEM` : Message système

**Statuts :**
- `SENT` : Envoyé
- `DELIVERED` : Livré
- `READ` : Lu
- `FAILED` : Échec
- `DELETED` : Supprimé

**Champs principaux :**
- `conversation` : Conversation associée
- `sender` : Expéditeur du message
- `message_type` : Type de message
- `content` : Contenu textuel
- `status` : Statut du message
- `parent` : Message parent (pour les réponses)
- `is_system_message` : Message généré par le système

#### 4. MessageAttachment
Modèle pour les pièces jointes des messages.

**Champs principaux :**
- `message` : Message associé
- `file` : Fichier joint
- `file_name` : Nom d'origine
- `file_size` : Taille en octets
- `file_type` : Type MIME
- `thumbnail` : Miniature (images/vidéos)

#### 5. MessageRead
Modèle de suivi des accusés de lecture.

**Champs principaux :**
- `message` : Message lu
- `user` : Utilisateur ayant lu
- `read_at` : Date/heure de lecture

### Services principaux

#### ConversationService
Service central pour la gestion des conversations.

#### MessageService
Service pour la gestion des messages et pièces jointes.

#### MessagingService
Service utilitaire pour les fonctionnalités transversales.

## Endpoints de l'API

### 1. Gestion des conversations

#### GET /api/conversations/
**Description :** Liste les conversations de l'utilisateur connecté

**Paramètres de filtrage :**
- `status` : Filtrer par statut (ACTIVE, ARCHIVED, DELETED)
- `type` : Filtrer par type (DIRECT, PROJECT, GROUP)
- `search` : Recherche dans titre, participants, projet, messages
- `project_id` : Filtrer par projet associé
- `ordering` : Tri (-last_message_at par défaut)

**Réponse :**
```json
{
  "count": 15,
  "next": "http://api.example.com/conversations/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": null,
      "conversation_type": "DIRECT",
      "status": "ACTIVE",
      "participant_count": 2,
      "project_title": null,
      "last_message_at": "2024-01-15T14:30:00Z",
      "unread_count": 3,
      "last_message": {
        "content": "Bonjour, j'aimerais discuter de votre projet...",
        "sender_name": "Marie Dubois",
        "created_at": "2024-01-15T14:30:00Z"
      },
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

#### POST /api/conversations/
**Description :** Créer une nouvelle conversation

**Corps de la requête :**
```json
{
  "conversation_type": "GROUP",
  "title": "Équipe Projet Mobile",
  "participant_ids": [
    "user-uuid-1",
    "user-uuid-2",
    "user-uuid-3"
  ],
  "project_id": "project-uuid" // Optionnel
}
```

**Réponse :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Équipe Projet Mobile",
  "conversation_type": "GROUP",
  "status": "ACTIVE",
  "participants": [
    {
      "id": "user-uuid-1",
      "first_name": "Jean",
      "last_name": "Dupont",
      "email": "jean@example.com"
    }
  ],
  "project": {
    "id": "project-uuid",
    "title": "Application Mobile"
  },
  "last_message_at": null,
  "unread_count": 0,
  "last_message": null,
  "created_at": "2024-01-15T15:00:00Z",
  "updated_at": "2024-01-15T15:00:00Z"
}
```

#### GET /api/conversations/{id}/
**Description :** Détails d'une conversation spécifique

#### PUT /api/conversations/{id}/
**Description :** Modifier une conversation (titre, statut)

#### DELETE /api/conversations/{id}/
**Description :** Supprimer une conversation (soft delete)

#### POST /api/conversations/direct/
**Description :** Créer ou récupérer une conversation directe

**Corps de la requête :**
```json
{
  "recipient_id": "user-uuid"
}
```

#### POST /api/conversations/{id}/add-participant/
**Description :** Ajouter un participant à une conversation

**Corps de la requête :**
```json
{
  "user_id": "user-uuid",
  "is_admin": false,
  "nickname": "Surnom optionnel"
}
```

#### POST /api/conversations/{id}/remove-participant/{participant_id}/
**Description :** Retirer un participant d'une conversation

#### POST /api/conversations/{id}/mark-as-read/
**Description :** Marquer tous les messages d'une conversation comme lus

**Réponse :**
```json
{
  "count": 5
}
```

#### GET /api/conversations/{id}/participants/
**Description :** Liste des participants d'une conversation

### 2. Gestion des messages

#### GET /api/conversations/{conversation_id}/messages/
**Description :** Liste les messages d'une conversation

**Paramètres de filtrage :**
- `search` : Recherche dans le contenu
- `type` : Filtrer par type de message
- `sender_id` : Filtrer par expéditeur
- `start_date` : Date de début
- `end_date` : Date de fin
- `limit` : Nombre de messages (défaut: 50)
- `offset` : Décalage pour pagination

**Réponse :**
```json
{
  "count": 127,
  "next": "http://api.example.com/conversations/123/messages/?offset=50",
  "previous": null,
  "results": [
    {
      "id": "msg-uuid",
      "conversation": "conv-uuid",
      "sender": {
        "id": "user-uuid",
        "first_name": "Jean",
        "last_name": "Dupont"
      },
      "message_type": "TEXT",
      "content": "Bonjour, comment allez-vous ?",
      "status": "READ",
      "parent": null,
      "is_system_message": false,
      "attachments": [],
      "read_by": [
        {
          "user": "user-uuid-2",
          "read_at": "2024-01-15T14:35:00Z"
        }
      ],
      "created_at": "2024-01-15T14:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

#### POST /api/conversations/{conversation_id}/messages/
**Description :** Envoyer un nouveau message

**Corps de la requête :**
```json
{
  "message_type": "TEXT",
  "content": "Voici mon message",
  "parent_id": "parent-msg-uuid", // Optionnel pour répondre
  "attachments": [
    {
      "file": "base64_encoded_file_data",
      "file_name": "document.pdf",
      "file_type": "application/pdf"
    }
  ]
}
```

#### GET /api/conversations/{conversation_id}/messages/{id}/
**Description :** Détails d'un message spécifique

#### PUT /api/conversations/{conversation_id}/messages/{id}/
**Description :** Modifier un message (dans les 15 minutes)

**Corps de la requête :**
```json
{
  "content": "Message modifié"
}
```

#### DELETE /api/conversations/{conversation_id}/messages/{id}/
**Description :** Supprimer un message (soft delete)

#### POST /api/conversations/{conversation_id}/messages/{id}/mark-as-read/
**Description :** Marquer un message comme lu

#### GET /api/conversations/{conversation_id}/messages/{id}/replies/
**Description :** Obtenir les réponses à un message

### 3. Gestion des pièces jointes

#### GET /api/conversations/{conversation_id}/messages/{message_id}/attachments/
**Description :** Liste des pièces jointes d'un message

**Réponse :**
```json
{
  "count": 2,
  "results": [
    {
      "id": "attachment-uuid",
      "message": "message-uuid",
      "file": "/media/messages/attachments/2024/01/15/document.pdf",
      "file_name": "Présentation Projet.pdf",
      "file_size": 2048576,
      "file_type": "application/pdf",
      "thumbnail": null,
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

#### GET /api/conversations/{conversation_id}/messages/{message_id}/attachments/{id}/
**Description :** Détails d'une pièce jointe

## Fonctionnalités avancées

### 1. Système d'accusés de lecture

Le système suit automatiquement qui a lu quels messages :
- Création automatique d'un accusé de lecture pour l'expéditeur
- Mise à jour du `last_read_at` du participant
- Calcul du nombre de messages non lus par conversation

### 2. Messages système

Les messages système sont générés automatiquement pour :
- Ajout/suppression de participants
- Changement de titre de conversation
- Événements liés aux projets

### 3. Réponses aux messages

Support des fils de discussion avec :
- Référence au message parent
- Récupération des réponses
- Navigation dans les fils

### 4. Recherche avancée

Recherche full-text dans :
- Contenu des messages
- Noms des participants
- Titres des conversations
- Projets associés

## Tâches asynchrones (Celery)

### Tâches disponibles

#### process_new_message
Traitement d'un nouveau message :
- Mise à jour de la conversation
- Envoi de notifications
- Indexation pour la recherche

#### process_message_attachments
Traitement des pièces jointes :
- Vérification de la taille
- Scan antivirus (simulation)
- Compression d'images
- Génération de miniatures

#### clean_old_messages
Nettoyage périodique :
- Suppression des messages supprimés > 30 jours
- Archivage des conversations inactives > 6 mois

#### create_project_conversation
Création automatique de conversations pour les projets.

#### send_conversation_digest
Envoi de résumés de conversations.

## Signaux Django automatiques

### Signaux configurés

1. **post_save Message** : Mise à jour `last_message_at` de la conversation
2. **post_save Message** : Création d'accusé de lecture pour l'expéditeur
3. **post_save MessageRead** : Mise à jour `last_read_at` du participant
4. **pre_save Message** : Gestion des changements de statut

## Gestion des permissions

### Permissions par endpoint

- **Conversations** : `IsAuthenticated` - accès limité aux conversations de l'utilisateur
- **Messages** : `IsAuthenticated` - accès limité aux messages des conversations de l'utilisateur
- **Modification** : Seul l'expéditeur peut modifier ses messages (15 min max)
- **Administration** : Les admins de conversation peuvent gérer les participants

### Sécurité

- Isolation stricte des données par participant
- Validation des permissions à chaque accès
- Limitation temporelle des modifications
- Logs détaillés des actions

## Intégration Frontend (Flutter/Dart)

### Service de messagerie

```dart
class MessagingService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Récupérer les conversations
  static Future<List<Conversation>> getConversations({
    String? status,
    String? type,
    String? search,
    int page = 1
  }) async {
    final queryParams = <String, String>{
      'page': page.toString(),
      if (status != null) 'status': status,
      if (type != null) 'type': type,
      if (search != null) 'search': search,
    };
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/conversations/').replace(
        queryParameters: queryParams
      ),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => Conversation.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement conversations');
  }
  
  // Créer une conversation directe
  static Future<Conversation> createDirectConversation(String recipientId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/conversations/direct/'),
      headers: await getAuthHeaders(),
      body: json.encode({
        'recipient_id': recipientId,
      }),
    );
    
    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = json.decode(response.body);
      return Conversation.fromJson(data);
    }
    throw Exception('Erreur création conversation');
  }
  
  // Récupérer les messages
  static Future<List<Message>> getMessages(
    String conversationId, {
    int limit = 50,
    int offset = 0,
    String? search,
  }) async {
    final queryParams = <String, String>{
      'limit': limit.toString(),
      'offset': offset.toString(),
      if (search != null) 'search': search,
    };
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/conversations/$conversationId/messages/').replace(
        queryParameters: queryParams
      ),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => Message.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement messages');
  }
  
  // Envoyer un message
  static Future<Message> sendMessage(
    String conversationId,
    String content, {
    String? parentId,
    List<MessageAttachment>? attachments,
  }) async {
    final body = <String, dynamic>{
      'content': content,
      'message_type': 'TEXT',
      if (parentId != null) 'parent_id': parentId,
      if (attachments != null) 'attachments': attachments.map((a) => a.toJson()).toList(),
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/api/conversations/$conversationId/messages/'),
      headers: await getAuthHeaders(),
      body: json.encode(body),
    );
    
    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      return Message.fromJson(data);
    }
    throw Exception('Erreur envoi message');
  }
  
  // Marquer comme lu
  static Future<bool> markMessageAsRead(String conversationId, String messageId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/conversations/$conversationId/messages/$messageId/mark-as-read/'),
      headers: await getAuthHeaders(),
    );
    
    return response.statusCode == 200;
  }
  
  // Marquer conversation comme lue
  static Future<int> markConversationAsRead(String conversationId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/conversations/$conversationId/mark-as-read/'),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['count'] as int;
    }
    throw Exception('Erreur marquage lecture');
  }
}
```

### Modèles Dart

```dart
class Conversation {
  final String id;
  final String? title;
  final String conversationType;
  final String status;
  final int participantCount;
  final String? projectTitle;
  final DateTime? lastMessageAt;
  final int unreadCount;
  final LastMessage? lastMessage;
  final DateTime createdAt;
  
  Conversation({
    required this.id,
    this.title,
    required this.conversationType,
    required this.status,
    required this.participantCount,
    this.projectTitle,
    this.lastMessageAt,
    required this.unreadCount,
    this.lastMessage,
    required this.createdAt,
  });
  
  factory Conversation.fromJson(Map<String, dynamic> json) {
    return Conversation(
      id: json['id'],
      title: json['title'],
      conversationType: json['conversation_type'],
      status: json['status'],
      participantCount: json['participant_count'],
      projectTitle: json['project_title'],
      lastMessageAt: json['last_message_at'] != null 
          ? DateTime.parse(json['last_message_at']) 
          : null,
      unreadCount: json['unread_count'],
      lastMessage: json['last_message'] != null 
          ? LastMessage.fromJson(json['last_message']) 
          : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  bool get hasUnreadMessages => unreadCount > 0;
  bool get isDirectMessage => conversationType == 'DIRECT';
  bool get isProjectConversation => conversationType == 'PROJECT';
  bool get isGroupConversation => conversationType == 'GROUP';
  
  String get displayTitle {
    if (title != null && title!.isNotEmpty) {
      return title!;
    }
    
    if (isProjectConversation && projectTitle != null) {
      return 'Projet: $projectTitle';
    }
    
    return 'Conversation';
  }
  
  IconData get typeIcon {
    switch (conversationType) {
      case 'DIRECT': return Icons.person;
      case 'PROJECT': return Icons.work;
      case 'GROUP': return Icons.group;
      default: return Icons.chat;
    }
  }
}

class LastMessage {
  final String content;
  final String senderName;
  final DateTime createdAt;
  
  LastMessage({
    required this.content,
    required this.senderName,
    required this.createdAt,
  });
  
  factory LastMessage.fromJson(Map<String, dynamic> json) {
    return LastMessage(
      content: json['content'],
      senderName: json['sender_name'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class Message {
  final String id;
  final String conversationId;
  final User? sender;
  final String messageType;
  final String content;
  final String status;
  final String? parentId;
  final bool isSystemMessage;
  final List<MessageAttachment> attachments;
  final List<MessageRead> readBy;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Message({
    required this.id,
    required this.conversationId,
    this.sender,
    required this.messageType,
    required this.content,
    required this.status,
    this.parentId,
    required this.isSystemMessage,
    required this.attachments,
    required this.readBy,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'],
      conversationId: json['conversation'],
      sender: json['sender'] != null ? User.fromJson(json['sender']) : null,
      messageType: json['message_type'],
      content: json['content'],
      status: json['status'],
      parentId: json['parent'],
      isSystemMessage: json['is_system_message'],
      attachments: (json['attachments'] as List)
          .map((a) => MessageAttachment.fromJson(a))
          .toList(),
      readBy: (json['read_by'] as List)
          .map((r) => MessageRead.fromJson(r))
          .toList(),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
  
  bool get isTextMessage => messageType == 'TEXT';
  bool get hasAttachments => attachments.isNotEmpty;
  bool get isReply => parentId != null;
  
  String get senderName {
    if (isSystemMessage) return 'Système';
    return sender?.getFullName() ?? 'Inconnu';
  }
  
  Color get statusColor {
    switch (status) {
      case 'SENT': return Colors.grey;
      case 'DELIVERED': return Colors.blue;
      case 'READ': return Colors.green;
      case 'FAILED': return Colors.red;
      default: return Colors.grey;
    }
  }
  
  IconData get typeIcon {
    switch (messageType) {
      case 'TEXT': return Icons.message;
      case 'IMAGE': return Icons.image;
      case 'FILE': return Icons.attach_file;
      case 'AUDIO': return Icons.audiotrack;
      case 'VIDEO': return Icons.videocam;
      case 'LOCATION': return Icons.location_on;
      case 'SYSTEM': return Icons.info;
      default: return Icons.message;
    }
  }
}

class MessageAttachment {
  final String id;
  final String messageId;
  final String file;
  final String fileName;
  final int fileSize;
  final String fileType;
  final String? thumbnail;
  final DateTime createdAt;
  
  MessageAttachment({
    required this.id,
    required this.messageId,
    required this.file,
    required this.fileName,
    required this.fileSize,
    required this.fileType,
    this.thumbnail,
    required this.createdAt,
  });
  
  factory MessageAttachment.fromJson(Map<String, dynamic> json) {
    return MessageAttachment(
      id: json['id'],
      messageId: json['message'],
      file: json['file'],
      fileName: json['file_name'],
      fileSize: json['file_size'],
      fileType: json['file_type'],
      thumbnail: json['thumbnail'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'file_name': fileName,
      'file_size': fileSize,
      'file_type': fileType,
    };
  }
  
  bool get isImage => fileType.startsWith('image/');
  bool get isVideo => fileType.startsWith('video/');
  bool get isAudio => fileType.startsWith('audio/');
  bool get isPdf => fileType == 'application/pdf';
  
  String get fileSizeFormatted {
    if (fileSize < 1024) {
      return '$fileSize octets';
    } else if (fileSize < 1024 * 1024) {
      return '${(fileSize / 1024).toStringAsFixed(1)} Ko';
    } else if (fileSize < 1024 * 1024 * 1024) {
      return '${(fileSize / (1024 * 1024)).toStringAsFixed(1)} Mo';
    } else {
      return '${(fileSize / (1024 * 1024 * 1024)).toStringAsFixed(1)} Go';
    }
  }
  
  IconData get fileIcon {
    if (isImage) return Icons.image;
    if (isVideo) return Icons.videocam;
    if (isAudio) return Icons.audiotrack;
    if (isPdf) return Icons.picture_as_pdf;
    return Icons.attach_file;
  }
}

class MessageRead {
  final String userId;
  final DateTime readAt;
  
  MessageRead({
    required this.userId,
    required this.readAt,
  });
  
  factory MessageRead.fromJson(Map<String, dynamic> json) {
    return MessageRead(
      userId: json['user'],
      readAt: DateTime.parse(json['read_at']),
    );
  }
}
```

### Interface utilisateur

```dart
class ConversationListScreen extends StatefulWidget {
  @override
  _ConversationListScreenState createState() => _ConversationListScreenState();
}

class _ConversationListScreenState extends State<ConversationListScreen> {
  List<Conversation> conversations = [];
  bool isLoading = true;
  String searchQuery = '';
  
  @override
  void initState() {
    super.initState();
    loadConversations();
  }
  
  Future<void> loadConversations() async {
    try {
      final result = await MessagingService.getConversations(
        search: searchQuery.isNotEmpty ? searchQuery : null,
      );
      setState(() {
        conversations = result;
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Erreur: $e')),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Messages'),
        actions: [
          IconButton(
            icon: Icon(Icons.search),
            onPressed: () => showSearch(
              context: context,
              delegate: ConversationSearchDelegate(),
            ),
          ),
        ],
      ),
      body: isLoading
          ? Center(child: CircularProgressIndicator())
          : conversations.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.chat_bubble_outline, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('Aucune conversation', style: TextStyle(fontSize: 18)),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: loadConversations,
                  child: ListView.builder(
                    itemCount: conversations.length,
                    itemBuilder: (context, index) {
                      final conversation = conversations[index];
                      return ConversationTile(
                        conversation: conversation,
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ChatScreen(conversation: conversation),
                          ),
                        ),
                      );
                    },
                  ),
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => NewConversationScreen()),
        ),
        child: Icon(Icons.add),
      ),
    );
  }
}

class ConversationTile extends StatelessWidget {
  final Conversation conversation;
  final VoidCallback onTap;
  
  const ConversationTile({
    Key? key,
    required this.conversation,
    required this.onTap,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: CircleAvatar(
        child: Icon(conversation.typeIcon),
        backgroundColor: conversation.hasUnreadMessages 
            ? Theme.of(context).primaryColor 
            : Colors.grey[300],
      ),
      title: Text(
        conversation.displayTitle,
        style: TextStyle(
          fontWeight: conversation.hasUnreadMessages 
              ? FontWeight.bold 
              : FontWeight.normal,
        ),
      ),
      subtitle: conversation.lastMessage != null
          ? Text(
              '${conversation.lastMessage!.senderName}: ${conversation.lastMessage!.content}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            )
          : Text('Aucun message'),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (conversation.lastMessageAt != null)
            Text(
              _formatTime(conversation.lastMessageAt!),
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
          if (conversation.hasUnreadMessages)
            Container(
              margin: EdgeInsets.only(top: 4),
              padding: EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${conversation.unreadCount}',
                style: TextStyle(color: Colors.white, fontSize: 12),
              ),
            ),
        ],
      ),
      onTap: onTap,
    );
  }
  
  String _formatTime(DateTime dateTime) {
    final now = DateTime.now();
    final difference = now.difference(dateTime);
    
    if (difference.inDays > 0) {
      return '${difference.inDays}j';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}h';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}min';
    } else {
      return 'maintenant';
    }
  }
}
```

## Codes de réponse HTTP

### Succès
- `200 OK` : Requête réussie
- `201 Created` : Ressource créée avec succès
- `204 No Content` : Suppression réussie

### Erreurs client
- `400 Bad Request` : Données invalides
- `401 Unauthorized` : Non authentifié
- `403 Forbidden` : Permissions insuffisantes
- `404 Not Found` : Ressource introuvable

### Erreurs serveur
- `500 Internal Server Error` : Erreur interne du serveur

## Support multi-langues

Le système supporte l'internationalisation avec :
- Messages d'erreur traduits
- Types et statuts localisés
- Messages système multilingues
- Interface utilisateur adaptée

## Monitoring et logs

### Logs disponibles
- Création/modification de conversations
- Envoi/réception de messages
- Gestion des pièces jointes
- Accusés de lecture
- Erreurs de traitement

### Métriques recommandées
- Volume de messages par jour
- Conversations actives
- Taux de lecture des messages
- Utilisation des pièces jointes
- Performance des recherches

## Limitations et quotas

### Limitations par défaut
- **Taille max pièce jointe** : 10 Mo
- **Messages par conversation** : Illimité
- **Participants par groupe** : 50 max
- **Modification message** : 15 minutes max
- **Recherche** : 1000 résultats max

### Optimisations performance
- Pagination des messages (50 par défaut)
- Cache des conversations récentes
- Indexation pour recherche full-text
- Compression automatique des images
- Nettoyage périodique des données

---

**Documentation mise à jour le :** 2024-01-15  
**Version de l'API :** 1.0  
**Contact technique :** dev@venturelink.com