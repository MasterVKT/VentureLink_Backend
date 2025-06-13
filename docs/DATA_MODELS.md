# Modèles de données VentureLink

## Vue d'ensemble

Ce document décrit les modèles de données utilisés dans l'API VentureLink. Chaque modèle représente une entité métier avec ses attributs, relations et contraintes.

## Conventions

### Champs communs
Tous les modèles héritent de `UUIDModel` et `TimeStampedModel` :

```json
{
  "id": "uuid4", // Identifiant unique
  "created_at": "2024-01-01T12:00:00Z", // Date de création
  "updated_at": "2024-01-01T12:00:00Z"  // Date de dernière modification
}
```

### Types de données
- **UUID**: Identifiant unique au format UUID4
- **DateTime**: Format ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)
- **Decimal**: Nombres décimaux pour les montants financiers
- **Money**: Montant avec précision décimale (12 chiffres, 2 décimales)

## Modèle User (Utilisateur)

### Structure
```json
{
  "id": "uuid4",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "user_type": "BOTH",
  "phone_number": "+33123456789",
  "location": "Paris, France",
  "language": "fr",
  "preferred_currency": "EUR",
  "is_verified": true,
  "is_premium": false,
  "is_staff": false,
  "is_active": true,
  "fcm_token": "firebase_cloud_messaging_token",
  "date_joined": "2024-01-01T12:00:00Z",
  "last_login": "2024-01-15T10:30:00Z"
}
```

### Énumérations
- **user_type**: `INVESTOR`, `PROJECT_OWNER`, `BOTH`, `ADMIN`
- **language**: `fr`, `en`
- **preferred_currency**: `EUR`, `USD`, `GBP`, `JPY`, `CAD`, `AUD`, `CHF`, `CNY`, `HKD`

### Contraintes
- Email unique et obligatoire
- Mot de passe minimum 8 caractères
- Numéro de téléphone au format international (+999999999)

## Modèle Profile (Profil utilisateur)

### Structure
```json
{
  "id": "uuid4",
  "user": "uuid4", // Relation OneToOne avec User
  "profile_picture": "http://example.com/media/profile.jpg",
  "cover_picture": "http://example.com/media/cover.jpg",
  "bio_short": "Entrepreneur passionné par l'innovation", // Max 280 caractères
  "title": "CEO & Founder",
  "website": "https://johndoe.com",
  "social_linkedin": "https://linkedin.com/in/johndoe",
  "social_twitter": "https://twitter.com/johndoe",
  "social_facebook": "https://facebook.com/johndoe",
  "views_count": 150,
  "avg_rating": 4.5, // Décimal 3,2
  "rating_count": 10,
  "verification_level": "VERIFIED",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### Énumérations
- **verification_level**: `BASIC`, `ADVANCED`, `VERIFIED`

### Relations
- **domain_expertise**: Liste des expertises (OneToMany)
- **project_interests**: Centres d'intérêt projet (OneToMany)
- **education**: Formations (OneToMany)
- **experience**: Expériences professionnelles (OneToMany)
- **badges**: Badges utilisateur (ManyToMany via UserBadge)

## Modèle Project (Projet)

### Structure
```json
{
  "id": "uuid4",
  "creator": "uuid4", // Relation ForeignKey vers User
  "title": "Application IA révolutionnaire",
  "short_description": "Une application qui révolutionne l'IA", // Max 280 caractères
  "full_description": "Description complète du projet...", // Text long
  "category": {
    "id": "uuid4",
    "name_fr": "Intelligence Artificielle",
    "name_en": "Artificial Intelligence",
    "icon": "ai-icon",
    "description_fr": "Projets liés à l'IA"
  },
  "stage": "PROTOTYPE",
  "status": "ACTIVE",
  "funding_min": 50000.00,
  "funding_max": 200000.00,
  "funding_currency": "EUR",
  "location_country": "France",
  "location_city": "Paris",
  "business_plan": "http://example.com/media/business_plan.pdf",
  "video_url": "https://youtube.com/watch?v=xxx",
  "is_premium": false,
  "is_featured": true,
  "is_draft": false,
  "views_count": 1500,
  "interests_count": 25,
  "favorites_count": 8,
  "published_at": "2024-01-02T10:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### Énumérations
- **stage**: `IDEA`, `PROTOTYPE`, `DEVELOPMENT`, `GROWTH`
- **status**: `ACTIVE`, `INACTIVE`, `FUNDED`, `ARCHIVED`

### Relations
- **tags**: Tags du projet (ManyToMany)
- **media**: Médias associés (OneToMany)
- **needs**: Besoins du projet (OneToMany)
- **skills_needed**: Compétences recherchées (OneToMany)
- **investments**: Investissements reçus (OneToMany)
- **conversations**: Discussions liées (OneToMany)

### Contraintes
- Titre minimum 10 caractères
- Description courte minimum 20 caractères
- Description complète minimum 100 caractères
- Montants de financement >= 0

## Modèle Investment (Investissement)

### Structure
```json
{
  "id": "uuid4",
  "investor": {
    "id": "uuid4",
    "email": "investor@example.com",
    "full_name": "Jane Smith"
  },
  "project": {
    "id": "uuid4",
    "title": "Application IA révolutionnaire"
  },
  "amount": 25000.00,
  "currency": "EUR",
  "investment_type": "EQUITY",
  "equity_percentage": 5.0, // Si type EQUITY
  "interest_rate": 8.5, // Si type LOAN, en pourcentage annuel
  "term_months": 24, // Si type LOAN, durée en mois
  "status": "APPROVED",
  "description": "Investissement stratégique dans l'IA",
  "contract_file": "http://example.com/media/contract.pdf",
  "notes": "Notes internes de l'investissement",
  "approved_at": "2024-01-15T10:00:00Z",
  "completed_at": null,
  "created_at": "2024-01-10T12:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Énumérations
- **investment_type**: `EQUITY`, `LOAN`, `DONATION`, `CONVERTIBLE_NOTE`
- **status**: `PENDING`, `APPROVED`, `REJECTED`, `CANCELLED`, `COMPLETED`

### Relations
- **history**: Historique des changements de statut (OneToMany)
- **payments**: Paiements associés (OneToMany)

### Contraintes
- Montant > 0
- Pourcentage d'actions entre 0.01 et 100
- Taux d'intérêt >= 0

## Modèle Conversation (Conversation)

### Structure
```json
{
  "id": "uuid4",
  "title": "Discussion sur le projet IA", // Optionnel
  "conversation_type": "PROJECT",
  "status": "ACTIVE",
  "project": {
    "id": "uuid4",
    "title": "Application IA révolutionnaire"
  }, // Optionnel
  "participants": [
    {
      "id": "uuid4",
      "user": {
        "id": "uuid4",
        "email": "user1@example.com",
        "full_name": "John Doe"
      },
      "is_admin": true,
      "last_read_at": "2024-01-15T14:30:00Z",
      "nickname": "John", // Optionnel
      "status": "ACTIVE",
      "muted_until": null
    }
  ],
  "last_message_at": "2024-01-15T14:35:00Z",
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-15T14:35:00Z"
}
```

### Énumérations
- **conversation_type**: `DIRECT`, `PROJECT`, `GROUP`
- **status**: `ACTIVE`, `ARCHIVED`, `DELETED`

### Relations
- **participants**: Participants via ConversationParticipant (ManyToMany)
- **messages**: Messages de la conversation (OneToMany)

## Modèle Message

### Structure
```json
{
  "id": "uuid4",
  "conversation": "uuid4",
  "sender": {
    "id": "uuid4",
    "email": "sender@example.com",
    "full_name": "John Doe"
  },
  "content": "Bonjour, je suis intéressé par votre projet",
  "message_type": "TEXT",
  "attachment": "http://example.com/media/file.pdf", // Optionnel
  "attachment_name": "document.pdf", // Nom original du fichier
  "attachment_size": 1024000, // Taille en bytes
  "is_edited": false,
  "is_deleted": false,
  "reply_to": "uuid4", // ID du message parent (optionnel)
  "reactions": [
    {
      "emoji": "👍",
      "count": 3,
      "users": ["uuid4", "uuid5"]
    }
  ],
  "read_by": [
    {
      "user": "uuid4",
      "read_at": "2024-01-15T14:30:00Z"
    }
  ],
  "created_at": "2024-01-15T14:25:00Z",
  "updated_at": "2024-01-15T14:25:00Z"
}
```

### Énumérations
- **message_type**: `TEXT`, `IMAGE`, `FILE`, `AUDIO`, `VIDEO`, `SYSTEM`

## Modèle Notification

### Structure
```json
{
  "id": "uuid4",
  "recipient": "uuid4",
  "title": "Nouvel investissement reçu",
  "content": "Vous avez reçu un investissement de 25 000€ de Jane Smith",
  "category": "INVESTMENT",
  "priority": "HIGH",
  "status": "UNREAD",
  "delivery_methods": ["PUSH", "EMAIL"],
  "delivered": true,
  "content_type": "investment", // Type d'objet lié
  "object_id": "uuid4", // ID de l'objet lié
  "action_url": "/investments/uuid4",
  "icon": "investment-icon",
  "read_at": null,
  "created_at": "2024-01-15T14:30:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### Énumérations
- **category**: `GENERAL`, `PROJECT`, `INVESTMENT`, `MESSAGE`, `PAYMENT`, `SYSTEM`
- **priority**: `LOW`, `NORMAL`, `HIGH`, `URGENT`
- **status**: `UNREAD`, `READ`, `ARCHIVED`
- **delivery_methods**: `PUSH`, `EMAIL`, `SMS`, `APP`

## Modèles de relation

### DomainExpertise (Expertise)
```json
{
  "id": "uuid4",
  "profile": "uuid4",
  "name": "Intelligence Artificielle",
  "years_experience": 5,
  "level": "EXPERT"
}
```

### Education (Formation)
```json
{
  "id": "uuid4",
  "profile": "uuid4",
  "institution": "École Polytechnique",
  "degree": "Ingénieur",
  "field_of_study": "Informatique",
  "start_year": 2018,
  "end_year": 2021,
  "description": "Formation d'ingénieur en informatique"
}
```

### Experience (Expérience professionnelle)
```json
{
  "id": "uuid4",
  "profile": "uuid4",
  "company": "Tech Corp",
  "title": "Développeur Senior",
  "location": "Paris, France",
  "current": false,
  "start_date": "2021-01", // Format YYYY-MM
  "end_date": "2023-12",
  "description": "Développement d'applications web"
}
```

### ProjectMedia (Média de projet)
```json
{
  "id": "uuid4",
  "project": "uuid4",
  "file": "http://example.com/media/image1.jpg",
  "media_type": "IMAGE",
  "title": "Screenshot principal",
  "description": "Interface utilisateur principale",
  "order": 1,
  "is_primary": true
}
```

### ProjectNeeds (Besoins de projet)
```json
{
  "id": "uuid4",
  "project": "uuid4",
  "need_type": "FUNDING",
  "amount": 100000.00,
  "currency": "EUR",
  "description": "Pour le développement MVP",
  "is_fulfilled": false,
  "priority": "HIGH"
}
```

### ProjectSkillsNeeded (Compétences recherchées)
```json
{
  "id": "uuid4",
  "project": "uuid4",
  "skill_name": "Développement Mobile",
  "experience_level": "SENIOR",
  "is_required": true,
  "description": "Développeur React Native expérimenté",
  "estimated_hours": 200
}
```

## Relations entre modèles

### User ↔ Project
- Un utilisateur peut créer plusieurs projets
- Un projet appartient à un utilisateur

### User ↔ Investment
- Un utilisateur (investisseur) peut faire plusieurs investissements
- Un investissement appartient à un investisseur

### Project ↔ Investment
- Un projet peut recevoir plusieurs investissements
- Un investissement est lié à un projet

### User ↔ Conversation
- Un utilisateur peut participer à plusieurs conversations
- Une conversation peut avoir plusieurs participants

### Conversation ↔ Message
- Une conversation peut contenir plusieurs messages
- Un message appartient à une conversation

### User ↔ Notification
- Un utilisateur peut recevoir plusieurs notifications
- Une notification est destinée à un utilisateur

## Contraintes d'intégrité

### Contraintes métier
1. Un utilisateur ne peut investir dans son propre projet
2. Un projet en brouillon (is_draft=true) ne peut recevoir d'investissements
3. Un investissement approuvé ne peut être modifié
4. Une conversation supprimée garde ses messages (soft delete)
5. Les montants financiers doivent être positifs

### Contraintes techniques
1. Les UUIDs sont utilisés comme clés primaires
2. Les relations ForeignKey utilisent PROTECT ou CASCADE selon le contexte
3. Les timestamps sont automatiquement gérés
4. Les champs obligatoires sont validés côté modèle et API

## Index de performance

### Index principaux
- User: email (unique)
- Project: creator, category, stage, status
- Investment: investor, project, status
- Message: conversation, sender, created_at
- Notification: recipient, status, category

Ces index optimisent les requêtes fréquentes de l'API et garantissent des performances optimales. 