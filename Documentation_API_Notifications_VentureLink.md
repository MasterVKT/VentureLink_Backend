# Documentation des APIs Notifications - VentureLink

## Vue d'ensemble

L'application **Notifications** de VentureLink gère un système complet de notifications multi-canal permettant d'informer les utilisateurs des événements importants de la plateforme. Le système supporte les notifications in-app, push (Firebase), email et SMS avec des préférences utilisateur granulaires.

## Architecture du système

### Modèles de données

#### 1. Notification
Modèle principal pour toutes les notifications envoyées aux utilisateurs.

**Champs principaux :**
- `recipient`: Utilisateur destinataire
- `title`: Titre de la notification  
- `content`: Contenu détaillé
- `category`: Catégorie (GENERAL, PROJECT, INVESTMENT, MESSAGE, PAYMENT, SYSTEM)
- `priority`: Priorité (LOW, NORMAL, HIGH, URGENT)
- `status`: Statut (UNREAD, READ, ARCHIVED, DELETED)
- `delivery_methods`: Méthodes de livraison (APP, EMAIL, SMS, PUSH)
- `related_object`: Objet lié via Generic Foreign Key
- `action_url`: URL d'action pour redirection
- `icon`: Icône à afficher

#### 2. NotificationTemplate
Templates réutilisables pour standardiser les notifications.

**Champs principaux :**
- `code`: Code unique d'identification
- `title_template`: Template du titre avec placeholders
- `content_template`: Template du contenu avec placeholders
- `category`: Catégorie par défaut
- `priority`: Priorité par défaut
- `default_delivery_methods`: Méthodes de livraison par défaut

#### 3. NotificationUserPreference
Préférences utilisateur pour personnaliser les notifications.

**Champs principaux :**
- `enable_email/push/sms/app`: Activation par méthode
- `project_notifications`: Notifications de projet
- `investment_notifications`: Notifications d'investissement
- `message_notifications`: Notifications de message
- `payment_notifications`: Notifications de paiement
- `system_notifications`: Notifications système
- `quiet_hours_start/end`: Heures silencieuses
- `minimum_priority`: Priorité minimale

### Services principaux

#### NotificationService
Service central pour la création et gestion des notifications.

#### FCMService
Service Firebase Cloud Messaging pour les notifications push.

#### EmailNotificationService
Service d'envoi d'emails avec templates HTML.

#### NotificationPreferencesService
Service de gestion des préférences utilisateur.

## Endpoints de l'API

### 1. Gestion des notifications

#### GET /api/notifications/
**Description :** Liste les notifications de l'utilisateur connecté

**Paramètres de filtrage :**
- `category`: Filtrer par catégorie
- `status`: Filtrer par statut
- `priority`: Filtrer par priorité
- `ordering`: Tri (-created_at par défaut)

**Réponse :**
```json
{
  "count": 25,
  "next": "http://api.example.com/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Nouvel investissement reçu !",
      "content": "John Doe a investi 5000 EUR dans votre projet: Application Mobile",
      "category": "INVESTMENT",
      "priority": "HIGH",
      "status": "UNREAD",
      "read_at": null,
      "icon": "investment",
      "action_url": "/projects/123/investments",
      "created_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

#### GET /api/notifications/{id}/
**Description :** Détails d'une notification spécifique

**Réponse :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "recipient": "user123",
  "title": "Nouvel investissement reçu !",
  "content": "John Doe a investi 5000 EUR dans votre projet: Application Mobile",
  "category": "INVESTMENT",
  "priority": "HIGH",
  "status": "UNREAD",
  "read_at": null,
  "delivery_methods": "APP,PUSH,EMAIL",
  "delivered": true,
  "content_type": "investment",
  "object_id": "inv_123",
  "action_url": "/projects/123/investments",
  "icon": "investment",
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

#### POST /api/notifications/{id}/mark_as_read/
**Description :** Marquer une notification comme lue

**Réponse :**
```json
{
  "status": "notification marked as read"
}
```

#### POST /api/notifications/{id}/archive/
**Description :** Archiver une notification

**Réponse :**
```json
{
  "status": "notification archived"
}
```

#### DELETE /api/notifications/{id}/
**Description :** Supprimer une notification (soft delete)

#### POST /api/notifications/mark_all_read/
**Description :** Marquer toutes les notifications comme lues

**Corps de la requête :**
```json
{
  "category": "PROJECT"  // Optionnel, pour filtrer par catégorie
}
```

**Réponse :**
```json
{
  "status": "15 notifications marked as read"
}
```

#### GET /api/notifications/unread_count/
**Description :** Obtenir le nombre de notifications non lues

**Réponse :**
```json
{
  "unread_count": 7
}
```

### 2. Templates de notification (Admin uniquement)

#### GET /api/notification-templates/
**Description :** Liste des templates de notification

**Paramètres de filtrage :**
- `category`: Filtrer par catégorie
- `is_active`: Filtrer par statut actif
- `search`: Recherche dans code, nom, description

#### POST /api/notification-templates/
**Description :** Créer un nouveau template

**Corps de la requête :**
```json
{
  "code": "INVESTMENT_RECEIVED",
  "name": "Investissement reçu",
  "category": "INVESTMENT",
  "title_template": "Nouvel investissement de {investor_name}",
  "content_template": "{investor_name} a investi {amount} {currency} dans votre projet: {project_title}",
  "priority": "HIGH",
  "default_icon": "investment",
  "default_delivery_methods": "APP,PUSH,EMAIL",
  "description": "Template pour notifier les créateurs de projet d'un nouvel investissement",
  "is_active": true
}
```

#### GET /api/notification-templates/{id}/
**Description :** Détails d'un template

#### PUT /api/notification-templates/{id}/
**Description :** Modifier un template

#### DELETE /api/notification-templates/{id}/
**Description :** Supprimer un template

### 3. Préférences de notification

#### GET /api/notification-preferences/
**Description :** Obtenir les préférences de l'utilisateur connecté

**Réponse :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user": "user123",
  "enable_email": true,
  "enable_push": true,
  "enable_sms": false,
  "enable_app": true,
  "project_notifications": true,
  "investment_notifications": true,
  "message_notifications": true,
  "payment_notifications": true,
  "system_notifications": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00",
  "minimum_priority": "NORMAL",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### PUT /api/notification-preferences/
**Description :** Modifier les préférences utilisateur

**Corps de la requête :**
```json
{
  "enable_email": true,
  "enable_push": false,
  "project_notifications": true,
  "investment_notifications": true,
  "message_notifications": false,
  "quiet_hours_start": "23:00:00",
  "quiet_hours_end": "07:00:00",
  "minimum_priority": "HIGH"
}
```

## Système d'événements automatiques

### Événements déclencheurs

Le système écoute automatiquement les événements suivants via des signaux Django :

1. **Nouveau message** (`Message` créé)
   - Notifie les participants de la conversation
   - Template : Message de {sender_name}

2. **Commentaire sur projet** (`ProjectComment` créé)  
   - Notifie le créateur du projet
   - Template : Nouveau commentaire sur votre projet

3. **Nouvel investissement** (`Investment` créé)
   - Notifie le créateur du projet
   - Template : Nouvel investissement reçu !

4. **Changement statut investissement** (`Investment` modifié)
   - Notifie l'investisseur
   - Template : Statut de votre investissement mis à jour

5. **Remboursement reçu** (`Repayment` créé)
   - Notifie l'investisseur
   - Template : Remboursement reçu

### Configuration des événements

Les événements sont configurés dans `apps/notifications/events.py` et utilisent les services de notification pour :
- Respecter les préférences utilisateur
- Choisir les canaux de livraison appropriés
- Générer le contenu contextuel
- Déclencher l'envoi asynchrone

## Tâches asynchrones (Celery)

### Tâches disponibles

#### send_notification_async
Envoi asynchrone d'une notification individuelle avec gestion des préférences.

#### send_bulk_notifications  
Envoi en masse de notifications à partir d'un template.

#### clean_old_notifications
Nettoyage périodique des anciennes notifications :
- Notifications lues > 30 jours
- Notifications très anciennes > 90 jours

#### send_digest_notifications
Envoi de résumés périodiques des notifications non lues.

#### send_project_notification
Notifications spécifiques aux projets.

#### send_message_notification
Notifications spécifiques aux messages.

## Services de livraison

### 1. Notifications Push (Firebase)

**Fonctionnalités :**
- Support Android et iOS
- Gestion des tokens d'appareil
- Envoi en batch (500 max par batch)
- Nettoyage automatique des tokens invalides
- Support des topics pour diffusion

**Configuration Android :**
```json
{
  "priority": "high",
  "icon": "ic_notification", 
  "color": "#1976D2",
  "sound": "default",
  "click_action": "FLUTTER_NOTIFICATION_CLICK"
}
```

**Configuration iOS :**
```json
{
  "badge": "unread_count",
  "sound": "default",
  "alert": {
    "title": "Titre",
    "body": "Contenu"
  }
}
```

### 2. Notifications Email

**Fonctionnalités :**
- Templates HTML responsive
- Contenu texte alternatif
- Personnalisation par utilisateur
- Lien de désabonnement automatique
- Support de l'envoi en masse

**Templates disponibles :**
- `notification_general.html`
- `notification_project.html`
- `notification_investment.html`
- `notification_message.html`
- `notification_payment.html`
- `welcome.html`
- `password_reset.html`

### 3. Notifications In-App

**Fonctionnalités :**
- Stockage en base de données
- Tri par priorité et date
- Filtrage avancé
- Actions contextuelles (marquer lu, archiver)
- Compteur de non-lues

## Gestion des permissions

### Permissions par endpoint

- **Notifications utilisateur** : `IsAuthenticated` - accès limité aux notifications de l'utilisateur
- **Templates** : `IsAuthenticated + IsAdminUser` - réservé aux administrateurs
- **Préférences** : `IsAuthenticated` - accès limité aux préférences de l'utilisateur

### Sécurité

- Isolation des données par utilisateur
- Validation stricte des entrées
- Logs détaillés des actions
- Gestion des erreurs gracieuse

## Intégration Frontend (Flutter/Dart)

### Configuration Firebase

```dart
// Initialisation FCM
FirebaseMessaging messaging = FirebaseMessaging.instance;

// Demander permissions iOS
NotificationSettings settings = await messaging.requestPermission(
  alert: true,
  announcement: false,
  badge: true,
  carPlay: false,
  criticalAlert: false,
  provisional: false,
  sound: true,
);

// Obtenir le token
String? token = await messaging.getToken();
// Envoyer le token au backend via API users
```

### Gestion des notifications

```dart
class NotificationService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Récupérer les notifications
  static Future<List<Notification>> getNotifications({
    String? category,
    String? status,
    int page = 1
  }) async {
    final queryParams = <String, String>{
      'page': page.toString(),
      if (category != null) 'category': category,
      if (status != null) 'status': status,
    };
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/notifications/').replace(
        queryParameters: queryParams
      ),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => Notification.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement notifications');
  }
  
  // Marquer comme lue
  static Future<bool> markAsRead(String notificationId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/notifications/$notificationId/mark_as_read/'),
      headers: await getAuthHeaders(),
    );
    
    return response.statusCode == 200;
  }
  
  // Obtenir le compteur
  static Future<int> getUnreadCount() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/notifications/unread_count/'),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['unread_count'] as int;
    }
    throw Exception('Erreur compteur notifications');
  }
  
  // Mettre à jour les préférences
  static Future<bool> updatePreferences(Map<String, dynamic> preferences) async {
    final response = await http.put(
      Uri.parse('$baseUrl/api/notification-preferences/'),
      headers: await getAuthHeaders(),
      body: json.encode(preferences),
    );
    
    return response.statusCode == 200;
  }
}
```

### Modèles Dart

```dart
class Notification {
  final String id;
  final String title;
  final String content;
  final String category;
  final String priority;
  final String status;
  final DateTime? readAt;
  final String? icon;
  final String? actionUrl;
  final DateTime createdAt;
  
  Notification({
    required this.id,
    required this.title,
    required this.content,
    required this.category,
    required this.priority,
    required this.status,
    this.readAt,
    this.icon,
    this.actionUrl,
    required this.createdAt,
  });
  
  factory Notification.fromJson(Map<String, dynamic> json) {
    return Notification(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      category: json['category'],
      priority: json['priority'],
      status: json['status'],
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
      icon: json['icon'],
      actionUrl: json['action_url'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  bool get isUnread => status == 'UNREAD';
  bool get isHighPriority => priority == 'HIGH' || priority == 'URGENT';
  
  Color get priorityColor {
    switch (priority) {
      case 'URGENT': return Colors.red;
      case 'HIGH': return Colors.orange;
      case 'NORMAL': return Colors.blue;
      case 'LOW': return Colors.grey;
      default: return Colors.blue;
    }
  }
  
  IconData get categoryIcon {
    switch (category) {
      case 'PROJECT': return Icons.work;
      case 'INVESTMENT': return Icons.attach_money;
      case 'MESSAGE': return Icons.message;
      case 'PAYMENT': return Icons.payment;
      case 'SYSTEM': return Icons.settings;
      default: return Icons.notifications;
    }
  }
}

class NotificationPreferences {
  final String id;
  final bool enableEmail;
  final bool enablePush;
  final bool enableSms;
  final bool enableApp;
  final bool projectNotifications;
  final bool investmentNotifications;
  final bool messageNotifications;
  final bool paymentNotifications;
  final bool systemNotifications;
  final TimeOfDay? quietHoursStart;
  final TimeOfDay? quietHoursEnd;
  final String minimumPriority;
  
  NotificationPreferences({
    required this.id,
    required this.enableEmail,
    required this.enablePush,
    required this.enableSms,
    required this.enableApp,
    required this.projectNotifications,
    required this.investmentNotifications,
    required this.messageNotifications,
    required this.paymentNotifications,
    required this.systemNotifications,
    this.quietHoursStart,
    this.quietHoursEnd,
    required this.minimumPriority,
  });
  
  factory NotificationPreferences.fromJson(Map<String, dynamic> json) {
    return NotificationPreferences(
      id: json['id'],
      enableEmail: json['enable_email'],
      enablePush: json['enable_push'],
      enableSms: json['enable_sms'],
      enableApp: json['enable_app'],
      projectNotifications: json['project_notifications'],
      investmentNotifications: json['investment_notifications'],
      messageNotifications: json['message_notifications'],
      paymentNotifications: json['payment_notifications'],
      systemNotifications: json['system_notifications'],
      quietHoursStart: json['quiet_hours_start'] != null 
          ? TimeOfDay.fromDateTime(DateTime.parse('2000-01-01 ${json['quiet_hours_start']}'))
          : null,
      quietHoursEnd: json['quiet_hours_end'] != null 
          ? TimeOfDay.fromDateTime(DateTime.parse('2000-01-01 ${json['quiet_hours_end']}'))
          : null,
      minimumPriority: json['minimum_priority'],
    );
  }
  
  Map<String, dynamic> toJson() {
    return {
      'enable_email': enableEmail,
      'enable_push': enablePush,
      'enable_sms': enableSms,
      'enable_app': enableApp,
      'project_notifications': projectNotifications,
      'investment_notifications': investmentNotifications,
      'message_notifications': messageNotifications,
      'payment_notifications': paymentNotifications,
      'system_notifications': systemNotifications,
      'quiet_hours_start': quietHoursStart?.format24Hour(),
      'quiet_hours_end': quietHoursEnd?.format24Hour(),
      'minimum_priority': minimumPriority,
    };
  }
}

extension TimeOfDayExtension on TimeOfDay {
  String format24Hour() {
    final hour = this.hour.toString().padLeft(2, '0');
    final minute = this.minute.toString().padLeft(2, '0');
    return '$hour:$minute:00';
  }
}
```

## Codes de réponse HTTP

### Succès
- `200 OK` : Requête réussie
- `201 Created` : Ressource créée avec succès

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
- Templates de notification multilingues
- Catégories et priorités localisées
- Emails dans la langue utilisateur

## Monitoring et logs

### Logs disponibles
- Création de notifications
- Envois push réussis/échoués
- Envois d'emails réussis/échoués
- Nettoyage des données
- Erreurs de service

### Métriques recommandées
- Taux de livraison par canal
- Temps de réponse des APIs
- Taux d'ouverture des notifications
- Préférences utilisateur populaires
- Volume de notifications par catégorie

---

**Documentation mise à jour le :** 2024-01-15  
**Version de l'API :** 1.0  
**Contact technique :** dev@venturelink.com