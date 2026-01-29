# Architecture Complète du Projet VentureLink

## Vue d'ensemble du projet

**VentureLink** est une plateforme complète de mise en relation entre entrepreneurs et investisseurs, développée avec Django REST Framework pour le backend et Flutter pour le frontend mobile. La plateforme facilite la création, la présentation et le financement de projets entrepreneuriaux à travers un écosystème intégré de 8 applications interconnectées.

### Technologies principales
- **Backend** : Django 4.x + Django REST Framework
- **Base de données** : PostgreSQL avec recherche full-text
- **Cache** : Redis pour les performances
- **Tâches asynchrones** : Celery + Redis
- **Authentification** : Firebase Auth + JWT
- **Paiements** : My-CoolPay API (sandbox/production)
- **Notifications** : Firebase Cloud Messaging + Email + SMS
- **Stockage** : AWS S3 pour les fichiers
- **Monitoring** : Sentry pour les erreurs

---

## 1. Application **Core** - Fondation Technique

### Description
L'application Core constitue la fondation technique de VentureLink, fournissant tous les composants transversaux, utilitaires et services partagés utilisés par les autres applications.

### Fonctionnalités implémentées

#### 1.1 Modèles abstraits de base
- **TimeStampedModel** : Champs automatiques `created_at` et `updated_at`
- **UUIDModel** : Clé primaire UUID v4 pour tous les modèles
- **MoneyField** : Champ monétaire standardisé (14 chiffres, 2 décimales, validation >= 0)

**Dépendances :** Aucune (modèles de base)

#### 1.2 Service de gestion des devises (CurrencyService)
- Récupération des taux de change via API externe
- Conversion automatique entre 20+ devises (EUR, USD, GBP, CAD, CHF, etc.)
- Cache des taux de change (24h)
- Formatage localisé des montants avec symboles

**Dépendances :**
- API externe de taux de change (exchangerate-api.com)
- Cache Redis pour la performance

#### 1.3 Service de paiement (MyCoolPayService)
- Intégration complète avec l'API My-CoolPay
- Support sandbox (développement) et production
- Création et gestion des paiements
- Vérification des statuts de paiement
- Gestion des remboursements partiels/complets
- Validation sécurisée des webhooks

**Dépendances :**
- API My-CoolPay externe
- Modèles Investment et InvestmentPayment (app investments)

#### 1.4 Middlewares personnalisés

##### FirebaseAuthenticationMiddleware
- Authentification automatique via tokens Firebase JWT
- Vérification transparente des en-têtes Authorization
- Mode développement avec vérification basique
- Logging détaillé des authentifications

**Dépendances :**
- Firebase Admin SDK
- Modèle User (app users)

##### CurrencyConversionMiddleware
- Conversion automatique des valeurs monétaires dans les réponses API
- Détection des champs monétaires (amount/currency, funding_min/funding_currency, etc.)
- Conversion selon les préférences utilisateur ou paramètres de requête
- Conservation des valeurs originales pour référence

**Dépendances :**
- CurrencyService
- Profil utilisateur (app users) pour les préférences

##### RequestLoggingMiddleware
- Logging détaillé des requêtes HTTP
- Métriques de performance (temps de réponse)
- Détection des adresses IP clients
- Monitoring des erreurs

**Dépendances :** Aucune

#### 1.5 Système de permissions granulaire
- **IsOwner** : Propriétaire uniquement
- **IsOwnerOrAdmin** : Propriétaire ou administrateur
- **IsOwnerOrReadOnly** : Propriétaire pour modification, lecture pour tous
- **IsAdminUser** : Administrateurs uniquement
- **IsProjectOwner** : Créateur du projet
- **IsInvestorOrProjectCreator** : Investisseur ou créateur du projet
- **IsPremiumUser** : Utilisateurs premium uniquement
- **IsVerifiedUser** : Utilisateurs vérifiés uniquement
- **ReadOnly** : Lecture seule

**Dépendances :**
- Modèle User (app users)
- Modèle Project (app projects)
- Modèle Investment (app investments)

#### 1.6 Gestion d'exceptions standardisée
- **VentureLinkException** : Exception de base
- **AuthenticationError** : Erreurs d'authentification
- **InvalidCredentialsError** : Identifiants invalides
- **TokenError** : Tokens invalides/expirés
- **PermissionDeniedError** : Permissions insuffisantes
- **ResourceNotFoundError** : Ressource introuvable
- **ValidationError** : Erreurs de validation
- **RateLimitExceededError** : Limite de requêtes dépassée
- **SubscriptionRequiredError** : Abonnement requis
- **PaymentError** : Erreurs de paiement
- Gestionnaire d'exceptions personnalisé avec formatage JSON standardisé

**Dépendances :** Aucune

#### 1.7 Utilitaires Firebase
- Vérification des tokens ID Firebase
- Récupération des informations utilisateur par UID
- Création de tokens personnalisés
- Envoi de notifications push FCM
- Mode développement avec vérification basique

**Dépendances :**
- Firebase Admin SDK
- Configuration Firebase du projet

#### 1.8 Tâches Celery d'analytics et maintenance
- **update_daily_analytics()** : Calcul des métriques quotidiennes
- **generate_user_engagement_report()** : Rapport d'engagement utilisateurs
- **generate_financial_analytics()** : Analytics financières
- **generate_weekly_summary_report()** : Rapport hebdomadaire
- **cleanup_old_analytics_data()** : Nettoyage des anciennes données
- **send_analytics_to_external_service()** : Envoi vers services externes

**Dépendances :**
- Tous les modèles des autres applications pour les métriques
- Service d'email pour les rapports
- Webhook externe optionnel

#### 1.9 Endpoints API
- **GET /api/core/currencies/** : Liste des devises disponibles
- **GET /api/core/test-sentry/** : Test d'intégration Sentry

**Dépendances :** CurrencyService

---

## 2. Application **Users** - Gestion des Utilisateurs

### Description
L'application Users gère l'ensemble du cycle de vie des utilisateurs, de l'inscription à la gestion des profils, en passant par l'authentification, les abonnements et les préférences.

### Fonctionnalités implémentées

#### 2.1 Modèle utilisateur personnalisé (User)
- Extension du modèle Django User
- Champs supplémentaires : `is_verified`, `is_premium`, `preferred_language`, `preferred_currency`
- Gestion des rôles et permissions
- Intégration Firebase UID

**Dépendances :**
- TimeStampedModel et UUIDModel (app core)

#### 2.2 Système d'authentification multi-canal

##### Authentification classique
- Inscription/connexion par email/mot de passe
- Validation d'email avec tokens sécurisés
- Réinitialisation de mot de passe
- Changement de mot de passe sécurisé

**Dépendances :**
- Service d'email (app core)
- Tokens de validation

##### Authentification Firebase
- Connexion via Firebase Auth (Google, Facebook, Apple, etc.)
- Synchronisation automatique des comptes
- Gestion des tokens JWT Firebase
- Création automatique de profils

**Dépendances :**
- Firebase Auth
- FirebaseAuthenticationMiddleware (app core)

#### 2.3 Gestion des profils utilisateur (Profile)
- Informations personnelles (nom, prénom, bio, photo)
- Localisation (pays, ville)
- Réseaux sociaux (LinkedIn, Twitter, website)
- Préférences (langue, devise, notifications)
- Statut de vérification et badges

**Dépendances :**
- Modèle User
- CurrencyService (app core) pour les devises

#### 2.4 Profils d'entreprise (CompanyProfile)
- Informations légales (nom, SIRET, adresse)
- Secteur d'activité et taille
- Membres de l'équipe
- Vérification administrative
- Documents légaux

**Dépendances :**
- Modèle User (créateur)
- Système de vérification administrative

#### 2.5 Système d'abonnements (Subscription)
- **Plan Gratuit** : Fonctionnalités de base
- **Plan Premium Mensuel** : Fonctionnalités avancées
- **Plan Premium Annuel** : Réduction et fonctionnalités premium
- Gestion des périodes d'essai
- Historique des transactions

**Dépendances :**
- MyCoolPayService (app core) pour les paiements
- Système de permissions premium

#### 2.6 Domaines d'expertise (DomainExpertise)
- Catégorisation des compétences
- Niveaux d'expertise (1-5)
- Validation par la communauté
- Recherche par expertise

**Dépendances :**
- Modèle User
- Système de validation communautaire

#### 2.7 Centres d'intérêt projets (ProjectInterest)
- Préférences sectorielles
- Montants d'investissement préférés
- Types d'investissement (equity, loan, etc.)
- Notifications ciblées

**Dépendances :**
- Modèle User
- Catégories de projets (app projects)

#### 2.8 Formation et expérience
- **Education** : Diplômes, établissements, années
- **Experience** : Postes, entreprises, durées
- Validation des informations
- Affichage chronologique

**Dépendances :**
- Modèle User
- Système de validation

#### 2.9 Système de badges (Badge)
- Badges de réussite (projets financés, investissements réussis)
- Badges de participation (messages, évaluations)
- Badges de vérification (email, téléphone, identité)
- Badges premium et exclusifs

**Dépendances :**
- Modèle User
- Métriques des autres applications (projects, investments, messaging)

#### 2.10 Endpoints API (25+ endpoints)
- **Authentification** : inscription, connexion, Firebase, réinitialisation
- **Profils** : CRUD complet, upload photos, réseaux sociaux
- **Entreprises** : création, gestion membres, vérification
- **Abonnements** : plans, checkout, historique
- **Préférences** : expertises, intérêts, notifications

**Dépendances :**
- Tous les services de l'app core
- Intégration avec les autres applications pour les métriques

---

## 3. Application **Projects** - Gestion des Projets

### Description
L'application Projects constitue le cœur métier de VentureLink, gérant la création, publication, recherche et interaction avec les projets entrepreneuriaux.

### Fonctionnalités implémentées

#### 3.1 Modèle principal Project
- **Stades de développement** : IDEA, PROTOTYPE, DEVELOPMENT, GROWTH
- **Statuts** : DRAFT, ACTIVE, INACTIVE, FUNDED, ARCHIVED
- Informations détaillées (titre, description, pitch, business plan)
- Financement (montant min/max, devise, type)
- Localisation géographique
- Dates importantes (création, publication, échéance)
- Flags (premium, vérifié, featured)

**Dépendances :**
- Modèle User (app users) pour le créateur
- TimeStampedModel et UUIDModel (app core)
- MoneyField (app core) pour les montants

#### 3.2 Système de catégorisation

##### ProjectCategory
- Catégories principales (Tech, Santé, Éducation, etc.)
- Support multilingue (FR/EN)
- Hiérarchie parent/enfant
- Icônes et couleurs

**Dépendances :**
- Système de traduction Django

##### ProjectTag
- Tags libres pour description fine
- Support multilingue
- Popularité et tendances
- Recherche et filtrage

**Dépendances :**
- Système de traduction Django

#### 3.3 Gestion des médias (ProjectMedia)
- **Types** : IMAGE, VIDEO, DOCUMENT, PRESENTATION
- Upload sécurisé vers AWS S3
- Gestion de l'ordre d'affichage
- Image principale automatique
- Compression et optimisation

**Dépendances :**
- Modèle Project
- AWS S3 pour le stockage
- Système de compression d'images

#### 3.4 Interactions utilisateur-projet

##### ProjectInteraction
- **Intérêts d'investissement** avec montant proposé
- **Favoris** pour suivi personnel
- **Questions/Réponses** entre investisseurs et créateurs
- Historique des interactions

**Dépendances :**
- Modèle Project
- Modèle User (app users)
- Système de notifications (app notifications)

#### 3.5 Besoins en ressources (ProjectNeeds)
- **Types** : INVESTMENT, LOAN, PARTNERSHIP, EXPERTISE, MATERIAL
- Descriptions détaillées des besoins
- Priorités et urgences
- Statuts de satisfaction

**Dépendances :**
- Modèle Project
- Système de matching avec profils utilisateurs

#### 3.6 Compétences requises (ProjectSkillsNeeded)
- Compétences spécifiques recherchées
- Niveaux requis (1-5)
- Descriptions des rôles
- Matching avec expertises utilisateurs

**Dépendances :**
- Modèle Project
- DomainExpertise (app users)

#### 3.7 Système de recherche et filtrage avancé
- **Recherche full-text** PostgreSQL sur titre, description, tags
- **Filtres multiples** : catégorie, stade, financement, localisation
- **Tri** : pertinence, date, popularité, financement
- **Géolocalisation** : recherche par proximité
- Cache Redis pour les performances

**Dépendances :**
- PostgreSQL avec extensions full-text
- Redis pour le cache
- Service de géolocalisation

#### 3.8 Collections spécialisées
- **Trending** : Projets populaires basés sur les interactions
- **Featured** : Projets mis en avant par l'équipe
- **My Projects** : Projets de l'utilisateur connecté
- **Related** : Projets similaires basés sur l'IA
- **Recently Viewed** : Historique de consultation

**Dépendances :**
- Analytics (app analytics) pour les métriques
- Algorithmes de recommandation
- Historique utilisateur

#### 3.9 Workflow de publication
1. **Création en brouillon** : Sauvegarde progressive
2. **Validation** : Vérification des champs obligatoires
3. **Publication** : Passage en statut ACTIVE
4. **Modération** : Vérification administrative optionnelle
5. **Promotion** : Mise en avant payante

**Dépendances :**
- Système de validation
- Modération administrative
- Système de paiement (app core) pour la promotion

#### 3.10 Gestion des permissions
- **Créateur** : Contrôle total sur son projet
- **Investisseurs** : Lecture et interaction
- **Administrateurs** : Modération et gestion
- **Utilisateurs premium** : Fonctionnalités avancées

**Dépendances :**
- Système de permissions (app core)
- Abonnements utilisateur (app users)

#### 3.11 Endpoints API (30+ endpoints)
- **CRUD projets** : création, lecture, mise à jour, suppression
- **Recherche** : filtres complexes, tri, pagination
- **Médias** : upload, gestion, optimisation
- **Interactions** : intérêts, favoris, questions
- **Collections** : trending, featured, related
- **Actions** : publication, archivage, promotion

**Dépendances :**
- Tous les services des autres applications
- Services externes (S3, géolocalisation)

---

## 4. Application **Investments** - Gestion des Investissements

### Description
L'application Investments constitue le cœur financier de VentureLink, gérant l'ensemble du cycle de vie des investissements, des demandes initiales aux remboursements finaux.

### Fonctionnalités implémentées

#### 4.1 Modèle principal Investment
- **Types d'investissement** : EQUITY (actions), LOAN (prêt), DONATION (don), CONVERTIBLE_NOTE (note convertible)
- **Statuts** : PENDING, APPROVED, REJECTED, CANCELLED, COMPLETED
- Montants et devises avec conversion automatique
- Conditions spécifiques (pourcentage d'actions, taux d'intérêt, durée)
- Documents contractuels
- Dates importantes (création, approbation, finalisation)

**Dépendances :**
- Modèle Project (app projects)
- Modèle User (app users) pour l'investisseur
- MoneyField et CurrencyService (app core)

#### 4.2 Historique des investissements (InvestmentHistory)
- Traçabilité complète des changements de statut
- Commentaires explicatifs pour chaque transition
- Utilisateur responsable du changement
- Horodatage précis

**Dépendances :**
- Modèle Investment
- Modèle User (app users)

#### 4.3 Gestion des paiements (InvestmentPayment)
- **Statuts** : PENDING, PROCESSING, COMPLETED, FAILED, REFUNDED
- **Méthodes** : BANK_TRANSFER, CREDIT_CARD, PAYPAL, CRYPTO, OTHER
- Intégration My-CoolPay pour le traitement
- Détails de transaction et reçus
- Paiements partiels et échelonnés

**Dépendances :**
- Modèle Investment
- MyCoolPayService (app core)
- Système de fichiers pour les reçus

#### 4.4 Système de remboursements (Repayment)
- **Types** : PRINCIPAL (capital), INTEREST (intérêts), DIVIDEND (dividende), MIXED (mixte)
- **Statuts** : PENDING, PROCESSING, COMPLETED, FAILED
- Calculs automatiques des montants
- Liens avec les échéanciers
- Notifications automatiques

**Dépendances :**
- Modèle Investment
- Modèle User (app users) pour payeur/bénéficiaire
- Système de notifications (app notifications)

#### 4.5 Échéanciers de remboursement (RepaymentSchedule)
- Planification automatique pour les prêts
- Calculs d'intérêts composés
- Gestion des échéances manquées
- Liens avec les remboursements effectifs
- Notifications de rappel

**Dépendances :**
- Modèle Investment
- Modèle Repayment
- Tâches Celery pour les rappels
- Système de notifications (app notifications)

#### 4.6 Workflow d'approbation
1. **Demande d'investissement** : Création par l'investisseur
2. **Évaluation** : Examen par le créateur du projet
3. **Négociation** : Échanges sur les conditions
4. **Approbation/Rejet** : Décision finale avec commentaires
5. **Paiement** : Traitement financier
6. **Finalisation** : Activation de l'investissement

**Dépendances :**
- Système de messaging (app messaging) pour négociation
- Système de notifications (app notifications)
- Services de paiement (app core)

#### 4.7 Calculs financiers automatiques

##### Pour les investissements en actions (EQUITY)
- Calcul du pourcentage de participation
- Validation des limites de dilution
- Gestion des droits de vote
- Calculs de valorisation

**Dépendances :**
- Modèle Project pour la valorisation
- Règles métier de dilution

##### Pour les prêts (LOAN)
- Génération automatique d'échéanciers
- Calculs d'intérêts simples/composés
- Gestion des paiements anticipés
- Pénalités de retard

**Dépendances :**
- Algorithmes financiers
- Configuration des taux d'intérêt

#### 4.8 Statistiques et analytics
- Métriques par utilisateur (total investi, nombre d'investissements)
- Métriques par projet (financement reçu, nombre d'investisseurs)
- Analyses de performance par type d'investissement
- Rapports de remboursement

**Dépendances :**
- Analytics (app analytics) pour le stockage
- Tâches Celery pour les calculs

#### 4.9 Gestion des risques
- Validation des montants et limites
- Vérification de la solvabilité
- Alertes sur les retards de paiement
- Système de notation des investisseurs

**Dépendances :**
- Profils utilisateur (app users)
- Historique des transactions
- Services externes de vérification

#### 4.10 Endpoints API (25+ endpoints)
- **CRUD investissements** : création, lecture, mise à jour
- **Gestion des statuts** : approbation, rejet, finalisation
- **Paiements** : création, suivi, remboursements
- **Échéanciers** : génération, gestion, liens
- **Statistiques** : métriques utilisateur et projet
- **URLs imbriquées** : navigation intuitive

**Dépendances :**
- Tous les services financiers
- Intégrations externes de paiement

---

## 5. Application **Messaging** - Système de Messagerie

### Description
L'application Messaging fournit un système de communication complet permettant aux utilisateurs d'échanger via des conversations directes, des discussions de projet et des groupes.

### Fonctionnalités implémentées

#### 5.1 Modèle principal Conversation
- **Types** : DIRECT (1-à-1), PROJECT (liées aux projets), GROUP (multi-participants)
- **Statuts** : ACTIVE, ARCHIVED, DELETED
- Métadonnées (titre, description, image)
- Gestion des participants
- Paramètres de confidentialité

**Dépendances :**
- Modèle User (app users) pour les participants
- Modèle Project (app projects) pour les conversations projet

#### 5.2 Gestion des participants (ConversationParticipant)
- Rôles (ADMIN, MODERATOR, MEMBER)
- Statuts (ACTIVE, MUTED, BANNED)
- Permissions granulaires
- Historique de participation
- Notifications personnalisées

**Dépendances :**
- Modèle Conversation
- Modèle User (app users)

#### 5.3 Système de messages (Message)
- **Types** : TEXT, IMAGE, FILE, AUDIO, VIDEO, LOCATION, SYSTEM
- Contenu riche avec formatage
- Pièces jointes multiples
- Messages système automatiques
- Édition et suppression

**Dépendances :**
- Modèle Conversation
- Modèle User (app users) pour l'expéditeur
- Stockage S3 pour les pièces jointes

#### 5.4 Gestion des pièces jointes (MessageAttachment)
- **Types** : IMAGE, DOCUMENT, AUDIO, VIDEO, OTHER
- Upload sécurisé vers S3
- Prévisualisation automatique
- Compression et optimisation
- Contrôle de taille et format

**Dépendances :**
- Modèle Message
- AWS S3 pour le stockage
- Services de compression

#### 5.5 Accusés de lecture (MessageRead)
- Suivi des messages lus par participant
- Indicateurs de lecture en temps réel
- Statistiques de lecture
- Notifications de lecture

**Dépendances :**
- Modèle Message
- Modèle User (app users)

#### 5.6 Messagerie temps réel
- WebSocket pour les messages instantanés
- Notifications push pour les messages
- Indicateurs de frappe en cours
- Statuts de présence en ligne

**Dépendances :**
- Django Channels pour WebSocket
- Firebase FCM (app core) pour les notifications push
- Redis pour la gestion des sessions

#### 5.7 Recherche dans les messages
- Recherche full-text dans le contenu
- Filtres par type, date, expéditeur
- Recherche dans les pièces jointes
- Historique de recherche

**Dépendances :**
- PostgreSQL full-text search
- Indexation des contenus

#### 5.8 Modération et sécurité
- Filtrage automatique des contenus inappropriés
- Signalement de messages
- Blocage d'utilisateurs
- Archivage automatique
- Chiffrement des messages sensibles

**Dépendances :**
- Services de modération IA
- Système de signalement
- Cryptographie pour le chiffrement

#### 5.9 Intégrations métier

##### Conversations de projet
- Création automatique lors d'intérêt d'investissement
- Participants automatiques (créateur + investisseur)
- Messages système pour les étapes importantes
- Liens vers les documents du projet

**Dépendances :**
- Modèle Project (app projects)
- Modèle Investment (app investments)
- Système de notifications (app notifications)

##### Négociations d'investissement
- Templates de messages pour négociation
- Suivi des conditions proposées
- Validation des accords
- Archivage automatique post-accord

**Dépendances :**
- Workflow d'investissement (app investments)
- Templates de contrats

#### 5.10 Analytics et métriques
- Volume de messages par période
- Taux de réponse des conversations
- Durée moyenne des conversations
- Analyse des sentiments

**Dépendances :**
- Analytics (app analytics)
- Services d'analyse de sentiment

#### 5.11 Endpoints API (20+ endpoints)
- **CRUD conversations** : création, gestion, archivage
- **Gestion participants** : ajout, suppression, rôles
- **Messages** : envoi, lecture, édition, suppression
- **Pièces jointes** : upload, téléchargement
- **Recherche** : messages, conversations, participants
- **WebSocket** : temps réel, présence

**Dépendances :**
- Services de stockage et compression
- Infrastructure temps réel

---

## 6. Application **Notifications** - Système de Notifications

### Description
L'application Notifications gère un système complet de notifications multi-canal permettant d'informer les utilisateurs des événements importants de la plateforme.

### Fonctionnalités implémentées

#### 6.1 Modèle principal Notification
- **Catégories** : GENERAL, PROJECT, INVESTMENT, MESSAGE, PAYMENT, SYSTEM
- **Priorités** : LOW, NORMAL, HIGH, URGENT
- **Statuts** : PENDING, SENT, DELIVERED, READ, FAILED
- Contenu riche (titre, message, données JSON)
- Liens d'action et deep links
- Expiration automatique

**Dépendances :**
- Modèle User (app users) pour le destinataire
- TimeStampedModel (app core)

#### 6.2 Templates de notifications (NotificationTemplate)
- Templates réutilisables par type d'événement
- Support multilingue (FR/EN)
- Variables dynamiques
- Personnalisation par canal
- Versioning des templates

**Dépendances :**
- Système de traduction Django
- Moteur de templates

#### 6.3 Préférences utilisateur (NotificationUserPreference)
- Préférences par catégorie et canal
- Horaires de réception (ne pas déranger)
- Fréquence des notifications (immédiat, groupé, quotidien)
- Désactivation sélective

**Dépendances :**
- Modèle User (app users)
- Modèle Notification

#### 6.4 Système multi-canal

##### Notifications in-app
- Affichage dans l'interface utilisateur
- Compteurs de notifications non lues
- Marquage automatique comme lues
- Historique persistant

**Dépendances :**
- Interface utilisateur frontend
- WebSocket pour temps réel

##### Notifications push (FCM)
- Envoi via Firebase Cloud Messaging
- Support iOS et Android
- Données personnalisées
- Gestion des tokens d'appareil
- Retry automatique en cas d'échec

**Dépendances :**
- Firebase FCM
- FCMService (app core)
- Tokens d'appareil utilisateur

##### Notifications email
- Templates HTML responsives
- Personnalisation par utilisateur
- Gestion des bounces et désabonnements
- Tracking d'ouverture et clics

**Dépendances :**
- EmailService (app core)
- Service SMTP configuré
- Templates email

##### Notifications SMS
- Envoi via API SMS
- Messages courts optimisés
- Gestion des numéros internationaux
- Coûts et limitations

**Dépendances :**
- Service SMS externe
- Validation des numéros de téléphone

#### 6.5 Déclencheurs automatiques

##### Événements de projet
- Nouveau projet publié dans catégories suivies
- Mise à jour de projet favori
- Nouveau commentaire ou question
- Changement de statut de financement

**Dépendances :**
- Signaux Django des modèles Project
- Préférences utilisateur (app users)

##### Événements d'investissement
- Nouvelle demande d'investissement reçue
- Changement de statut d'investissement
- Échéance de remboursement approchant
- Paiement reçu ou échoué

**Dépendances :**
- Signaux Django des modèles Investment
- Tâches Celery pour les échéances

##### Événements de messagerie
- Nouveau message reçu
- Mention dans une conversation
- Invitation à rejoindre un groupe
- Message non lu depuis X temps

**Dépendances :**
- Signaux Django des modèles Message
- Tâches Celery pour les rappels

##### Événements système
- Mise à jour de l'application
- Maintenance programmée
- Changements de conditions d'utilisation
- Alertes de sécurité

**Dépendances :**
- Configuration système
- Tâches administratives

#### 6.6 Gestion intelligente
- Groupement des notifications similaires
- Limitation du spam (max par heure/jour)
- Respect des fuseaux horaires
- Optimisation des heures d'envoi
- A/B testing des templates

**Dépendances :**
- Profils utilisateur pour les fuseaux horaires
- Analytics pour l'optimisation

#### 6.7 Tâches asynchrones
- **send_notification_batch()** : Envoi en masse
- **cleanup_old_notifications()** : Nettoyage automatique
- **process_notification_queue()** : Traitement de la file
- **update_notification_stats()** : Mise à jour des statistiques

**Dépendances :**
- Celery pour l'asynchrone
- Redis pour la file d'attente

#### 6.8 Analytics et métriques
- Taux de livraison par canal
- Taux d'ouverture et de clic
- Préférences utilisateur populaires
- Performance des templates
- Coûts par canal

**Dépendances :**
- Analytics (app analytics)
- Services de tracking externes

#### 6.9 Endpoints API (15+ endpoints)
- **CRUD notifications** : liste, détail, marquage lu
- **Préférences** : gestion des préférences utilisateur
- **Templates** : gestion administrative
- **Statistiques** : métriques et rapports
- **Test** : envoi de notifications de test

**Dépendances :**
- Tous les services de notification
- Système d'administration

---

## 7. Application **Analytics** - Métriques et Tableaux de Bord

### Description
L'application Analytics fournit un système complet de collecte, analyse et visualisation des métriques de la plateforme pour les utilisateurs et les administrateurs.

### Fonctionnalités implémentées

#### 7.1 Métriques utilisateur (UserMetrics)
- Nombre de projets créés/suivis
- Montant total investi/reçu
- Nombre de messages envoyés/reçus
- Score d'engagement et d'activité
- Évolution temporelle des métriques

**Dépendances :**
- Modèle User (app users)
- Tous les modèles des autres applications pour les calculs

#### 7.2 Métriques de projet (ProjectMetrics)
- Nombre de vues et d'interactions
- Montant de financement reçu
- Nombre d'investisseurs
- Taux de conversion visiteur → investisseur
- Analyse géographique des intérêts

**Dépendances :**
- Modèle Project (app projects)
- Modèles Investment et ProjectInteraction

#### 7.3 Métriques quotidiennes (DailyMetrics)
- Utilisateurs actifs quotidiens (DAU)
- Nouveaux utilisateurs et projets
- Volume de messages et notifications
- Transactions financières
- Métriques de performance technique

**Dépendances :**
- Tous les modèles pour les calculs quotidiens
- Tâches Celery pour la génération automatique

#### 7.4 Journal d'événements (EventLog)
- Tracking détaillé des actions utilisateur
- Événements système et erreurs
- Parcours utilisateur complets
- Données pour l'analyse comportementale
- Respect RGPD avec anonymisation

**Dépendances :**
- Middleware de tracking (app core)
- Système d'anonymisation

#### 7.5 Suivi des parrainages (ReferralTracker)
- Codes de parrainage uniques
- Tracking des conversions
- Récompenses automatiques
- Analyse de viralité
- Rapports de performance

**Dépendances :**
- Modèle User (app users)
- Système de récompenses

#### 7.6 Services d'analytics

##### MetricsService
- Calculs de métriques en temps réel
- Agrégations par période
- Comparaisons temporelles
- Prédictions basées sur les tendances
- Export de données

**Dépendances :**
- Tous les modèles de données
- Algorithmes de calcul

##### EventTrackingService
- Capture d'événements en temps réel
- Filtrage et validation des données
- Stockage optimisé
- Anonymisation automatique
- Intégration avec services externes

**Dépendances :**
- Middleware de tracking
- Services externes d'analytics

#### 7.7 Tableaux de bord

##### Dashboard utilisateur
- Vue d'ensemble de l'activité personnelle
- Métriques de projets et investissements
- Recommandations personnalisées
- Objectifs et progression

**Dépendances :**
- Métriques utilisateur personnelles
- Algorithmes de recommandation

##### Dashboard administrateur
- Métriques globales de la plateforme
- Analyses de croissance et rétention
- Détection d'anomalies
- Rapports financiers
- Monitoring technique

**Dépendances :**
- Toutes les métriques de la plateforme
- Services de monitoring

#### 7.8 Rapports automatisés
- Rapports quotidiens/hebdomadaires/mensuels
- Envoi automatique par email
- Personnalisation par rôle
- Export en PDF/Excel
- Archivage automatique

**Dépendances :**
- Système d'email (app core)
- Générateur de PDF
- Tâches Celery pour l'automatisation

#### 7.9 Intégrations externes
- Google Analytics pour le web
- Mixpanel pour l'analyse comportementale
- Amplitude pour les funnels
- Webhooks pour services tiers
- API pour outils BI

**Dépendances :**
- APIs des services externes
- Configuration des webhooks

#### 7.10 Optimisations performance
- Cache Redis pour les métriques fréquentes
- Pré-calcul des agrégations
- Indexation optimisée des requêtes
- Pagination intelligente
- Compression des données historiques

**Dépendances :**
- Redis pour le cache
- Optimisations base de données

#### 7.11 Endpoints API (15+ endpoints)
- **Métriques utilisateur** : dashboard personnel, progression
- **Métriques projet** : analytics détaillées par projet
- **Métriques globales** : dashboard administrateur
- **Événements** : tracking et historique
- **Rapports** : génération et export
- **Top listes** : projets populaires, utilisateurs actifs

**Dépendances :**
- Tous les services d'analytics
- Services d'export et génération

---

## 8. Application **Content** - Gestion de Contenu

### Description
L'application Content gère l'ensemble du contenu éditorial et informatif de la plateforme, incluant les articles, guides, FAQ et pages statiques.

### Fonctionnalités implémentées

#### 8.1 Système d'articles et blog
- Articles éditoriaux sur l'entrepreneuriat
- Guides pratiques pour les utilisateurs
- Actualités de la plateforme
- Contenu SEO optimisé
- Support multilingue (FR/EN)

**Dépendances :**
- Modèle User (app users) pour les auteurs
- Système de traduction Django
- SEO et référencement

#### 8.2 Base de connaissances (FAQ)
- Questions fréquemment posées
- Catégorisation par sujet
- Recherche dans la base
- Votes d'utilité
- Suggestions automatiques

**Dépendances :**
- Système de recherche full-text
- Analytics pour les suggestions

#### 8.3 Pages statiques
- Conditions d'utilisation
- Politique de confidentialité
- À propos de l'entreprise
- Contact et support
- Landing pages marketing

**Dépendances :**
- Système de templates
- Gestion des versions

#### 8.4 Gestion éditoriale
- Workflow de publication (brouillon → révision → publication)
- Système de révision et approbation
- Planification de publication
- Archivage automatique
- Versioning du contenu

**Dépendances :**
- Système de permissions éditoriales
- Tâches Celery pour la planification

#### 8.5 Optimisation SEO
- Méta-données automatiques
- URLs optimisées
- Sitemap automatique
- Schema.org markup
- Analyse de performance SEO

**Dépendances :**
- Services SEO externes
- Analytics web

#### 8.6 Intégration avec les autres applications
- Liens vers projets et utilisateurs
- Recommandations de contenu basées sur l'activité
- Notifications de nouveau contenu
- Partage social automatique

**Dépendances :**
- Modèles des autres applications
- Services de partage social
- Système de notifications (app notifications)

---

## Dépendances Inter-Applications

### Matrice des dépendances principales

| Application | Dépend de | Utilisé par |
|-------------|-----------|-------------|
| **Core** | Aucune (base) | Toutes les autres |
| **Users** | Core | Toutes les autres |
| **Projects** | Core, Users | Investments, Messaging, Analytics |
| **Investments** | Core, Users, Projects | Analytics, Notifications |
| **Messaging** | Core, Users, Projects, Investments | Notifications, Analytics |
| **Notifications** | Core, Users, toutes les autres | Analytics |
| **Analytics** | Toutes les autres | Aucune (consommateur final) |
| **Content** | Core, Users | Notifications, Analytics |

### Flux de données critiques

#### 1. Flux d'investissement
```
Users → Projects → Investments → Payments (Core) → Notifications → Analytics
```

#### 2. Flux de communication
```
Users → Projects → Messaging → Notifications → Analytics
```

#### 3. Flux d'analytics
```
Toutes les apps → Analytics → Rapports → Notifications (email)
```

#### 4. Flux d'authentification
```
Firebase (externe) → Core (middleware) → Users → Toutes les apps
```

### Services externes critiques

1. **Firebase** : Authentification, notifications push, configuration
2. **My-CoolPay** : Traitement des paiements et remboursements
3. **AWS S3** : Stockage des fichiers et médias
4. **API de change** : Taux de conversion des devises
5. **Services SMS/Email** : Notifications multi-canal
6. **PostgreSQL** : Base de données principale avec recherche full-text
7. **Redis** : Cache et files d'attente Celery

### Points de défaillance et résilience

#### Points critiques
- **Firebase** : Authentification de tous les utilisateurs
- **Base de données** : Stockage de toutes les données
- **Redis** : Cache et tâches asynchrones
- **My-CoolPay** : Traitement des paiements

#### Mécanismes de résilience
- **Mode dégradé** : Fonctionnement sans services externes
- **Cache** : Réduction de la charge sur la base de données
- **Retry automatique** : Pour les services externes
- **Monitoring** : Détection proactive des problèmes
- **Backup** : Sauvegarde automatique des données critiques

---

## Conclusion

VentureLink représente un écosystème complet et interconnecté de 8 applications Django, chacune ayant des responsabilités spécifiques mais travaillant ensemble pour offrir une expérience utilisateur cohérente. L'architecture modulaire permet une maintenance facilitée, une scalabilité horizontale et une évolution indépendante de chaque composant.

La plateforme gère l'ensemble du cycle de vie entrepreneurial, de la création de projet au financement, en passant par la communication et le suivi, avec des fonctionnalités avancées d'analytics et de gestion de contenu. L'intégration de services externes (Firebase, My-CoolPay, AWS) assure une expérience moderne et sécurisée pour tous les utilisateurs.

**Total des fonctionnalités implémentées :**
- **150+ endpoints API** documentés
- **50+ modèles de données** interconnectés
- **Multi-devises** avec conversion temps réel
- **Multi-langues** (FR/EN) complet
- **Notifications multi-canal** (in-app, push, email, SMS)
- **Système de paiement** intégré et sécurisé
- **Analytics avancées** avec rapports automatisés
- **Recherche full-text** et filtrage avancé
- **Gestion de fichiers** optimisée (S3)
- **Authentification moderne** (Firebase + JWT)

La plateforme est prête pour le déploiement en production et l'intégration avec le frontend Flutter.