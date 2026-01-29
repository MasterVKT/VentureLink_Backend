# Documentation des APIs Investments - VentureLink

## Vue d'ensemble

L'application **Investments** de VentureLink constitue le cœur métier de la plateforme, gérant l'ensemble du cycle de vie des investissements entre entrepreneurs et investisseurs. Le système supporte différents types d'investissements (actions, prêts, dons, notes convertibles), la gestion des paiements, les remboursements et les échéanciers.

## Architecture du système

### Modèles de données

#### 1. Investment
Modèle principal représentant un investissement d'un utilisateur dans un projet.

**Types d'investissement :**
- `EQUITY` : Actions (participation au capital)
- `LOAN` : Prêt avec intérêts
- `DONATION` : Don sans contrepartie
- `CONVERTIBLE_NOTE` : Note convertible en actions

**Statuts :**
- `PENDING` : En attente d'approbation
- `APPROVED` : Approuvé par le créateur du projet
- `REJECTED` : Rejeté
- `CANCELLED` : Annulé par l'investisseur
- `COMPLETED` : Finalisé (paiement effectué)

**Champs principaux :**
- `investor` : Utilisateur investisseur
- `project` : Projet cible
- `amount` : Montant de l'investissement
- `currency` : Devise (EUR, USD, etc.)
- `investment_type` : Type d'investissement
- `equity_percentage` : Pourcentage d'actions (si applicable)
- `interest_rate` : Taux d'intérêt annuel (si applicable)
- `term_months` : Durée en mois (pour les prêts)
- `status` : Statut actuel
- `contract_file` : Document contractuel
- `approved_at` : Date d'approbation
- `completed_at` : Date de finalisation

#### 2. InvestmentHistory
Historique des changements de statut d'un investissement.

**Champs principaux :**
- `investment` : Investissement concerné
- `user` : Utilisateur ayant effectué le changement
- `old_status` : Ancien statut
- `new_status` : Nouveau statut
- `comment` : Commentaire explicatif

#### 3. InvestmentPayment
Gestion des paiements liés aux investissements.

**Statuts :**
- `PENDING` : En attente
- `PROCESSING` : En traitement
- `COMPLETED` : Complété
- `FAILED` : Échoué
- `REFUNDED` : Remboursé

**Méthodes de paiement :**
- `BANK_TRANSFER` : Virement bancaire
- `CREDIT_CARD` : Carte de crédit
- `PAYPAL` : PayPal
- `CRYPTO` : Cryptomonnaie
- `OTHER` : Autre

**Champs principaux :**
- `investment` : Investissement associé
- `amount` : Montant du paiement
- `currency` : Devise
- `payment_method` : Méthode de paiement
- `status` : Statut du paiement
- `transaction_id` : ID de transaction externe
- `payment_details` : Détails JSON du paiement
- `receipt_file` : Reçu de paiement

#### 4. Repayment
Modèle pour les remboursements des investisseurs.

**Types de remboursement :**
- `PRINCIPAL` : Remboursement du capital
- `INTEREST` : Paiement d'intérêts
- `DIVIDEND` : Dividende
- `MIXED` : Mixte (capital + intérêts)

**Champs principaux :**
- `investment` : Investissement concerné
- `paid_by` : Utilisateur payeur (créateur du projet)
- `received_by` : Utilisateur bénéficiaire (investisseur)
- `amount` : Montant total
- `currency` : Devise
- `repayment_type` : Type de remboursement
- `principal_amount` : Montant du capital
- `interest_amount` : Montant des intérêts
- `status` : Statut du remboursement
- `payment_method` : Méthode de paiement
- `transaction_id` : ID de transaction
- `receipt_file` : Reçu de paiement

#### 5. RepaymentSchedule
Échéancier de remboursement pour les prêts.

**Champs principaux :**
- `investment` : Investissement concerné
- `due_date` : Date d'échéance
- `amount` : Montant total de l'échéance
- `principal_amount` : Partie capital
- `interest_amount` : Partie intérêts
- `currency` : Devise
- `is_paid` : Statut de paiement
- `repayment` : Remboursement associé (si payé)

### Services principaux

#### InvestmentService
Service central pour la gestion des investissements.

#### RepaymentService
Service pour la gestion des remboursements.

#### RepaymentScheduleService
Service pour la gestion des échéanciers.

## Endpoints de l'API

### 1. Gestion des investissements

#### GET /api/investments/
**Description :** Liste les investissements accessibles à l'utilisateur

**Paramètres de filtrage :**
- `project_id` : Filtrer par projet
- `status` : Filtrer par statut
- `investment_type` : Filtrer par type d'investissement
- `ordering` : Tri (-created_at par défaut)

**Réponse :**
```json
{
  "count": 25,
  "next": "http://api.example.com/investments/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "investor": {
        "id": "user-uuid",
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean@example.com"
      },
      "project": {
        "id": "project-uuid",
        "title": "Application Mobile Innovante",
        "creator": "Marie Martin"
      },
      "amount": "50000.00",
      "currency": "EUR",
      "investment_type": "EQUITY",
      "equity_percentage": "5.00",
      "status": "APPROVED",
      "created_at": "2024-01-15T10:00:00Z",
      "approved_at": "2024-01-16T14:30:00Z"
    }
  ]
}
```

#### POST /api/investments/
**Description :** Créer un nouvel investissement

**Corps de la requête :**
```json
{
  "project_id": "project-uuid",
  "amount": "50000.00",
  "currency": "EUR",
  "investment_type": "EQUITY",
  "equity_percentage": "5.00",
  "description": "Investissement dans le développement de l'application mobile"
}
```

**Réponse :**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "investor": {
    "id": "user-uuid",
    "first_name": "Jean",
    "last_name": "Dupont"
  },
  "project": {
    "id": "project-uuid",
    "title": "Application Mobile Innovante"
  },
  "amount": "50000.00",
  "currency": "EUR",
  "investment_type": "EQUITY",
  "equity_percentage": "5.00",
  "interest_rate": null,
  "term_months": null,
  "status": "PENDING",
  "description": "Investissement dans le développement de l'application mobile",
  "contract_file": null,
  "approved_at": null,
  "completed_at": null,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

#### GET /api/investments/{id}/
**Description :** Détails d'un investissement spécifique

#### PUT /api/investments/{id}/
**Description :** Modifier un investissement (uniquement si statut PENDING)

#### PATCH /api/investments/{id}/update_status/
**Description :** Mettre à jour le statut d'un investissement (créateur du projet uniquement)

**Corps de la requête :**
```json
{
  "status": "APPROVED",
  "comment": "Investissement approuvé après validation du dossier"
}
```

#### GET /api/investments/{id}/history/
**Description :** Historique des changements de statut

**Réponse :**
```json
[
  {
    "id": "history-uuid",
    "investment": "investment-uuid",
    "user": {
      "id": "user-uuid",
      "first_name": "Marie",
      "last_name": "Martin"
    },
    "old_status": "PENDING",
    "new_status": "APPROVED",
    "comment": "Investissement approuvé après validation du dossier",
    "created_at": "2024-01-16T14:30:00Z"
  }
]
```

#### GET /api/investments/{id}/payments/
**Description :** Liste des paiements d'un investissement

#### POST /api/investments/{id}/create_payment/
**Description :** Créer un paiement pour un investissement

**Corps de la requête :**
```json
{
  "amount": "50000.00",
  "currency": "EUR",
  "payment_method": "BANK_TRANSFER",
  "transaction_id": "TXN123456789",
  "payment_details": {
    "bank_name": "Banque Exemple",
    "account_number": "FR76 1234 5678 9012 3456 7890 123"
  },
  "notes": "Virement effectué le 15/01/2024"
}
```

#### GET /api/investments/stats/
**Description :** Statistiques d'investissement de l'utilisateur connecté

**Réponse :**
```json
{
  "total_invested": "150000.00",
  "total_investments": 5,
  "pending_investments": 1,
  "approved_investments": 3,
  "completed_investments": 1,
  "by_type": {
    "EQUITY": {
      "count": 3,
      "total_amount": "120000.00"
    },
    "LOAN": {
      "count": 2,
      "total_amount": "30000.00"
    }
  },
  "by_currency": {
    "EUR": "120000.00",
    "USD": "30000.00"
  }
}
```

### 2. Gestion des paiements

#### GET /api/payments/
**Description :** Liste des paiements d'investissement

#### GET /api/payments/{id}/
**Description :** Détails d'un paiement

#### PATCH /api/payments/{id}/update_status/
**Description :** Mettre à jour le statut d'un paiement

**Corps de la requête :**
```json
{
  "status": "COMPLETED"
}
```

### 3. Gestion des remboursements

#### GET /api/repayments/
**Description :** Liste les remboursements accessibles à l'utilisateur

**Paramètres de filtrage :**
- `investment_id` : Filtrer par investissement
- `status` : Filtrer par statut
- `repayment_type` : Filtrer par type de remboursement

**Réponse :**
```json
{
  "count": 10,
  "results": [
    {
      "id": "repayment-uuid",
      "investment": {
        "id": "investment-uuid",
        "project_title": "Application Mobile",
        "investor_name": "Jean Dupont"
      },
      "paid_by": {
        "id": "creator-uuid",
        "first_name": "Marie",
        "last_name": "Martin"
      },
      "received_by": {
        "id": "investor-uuid",
        "first_name": "Jean",
        "last_name": "Dupont"
      },
      "amount": "2500.00",
      "currency": "EUR",
      "repayment_type": "INTEREST",
      "principal_amount": "0.00",
      "interest_amount": "2500.00",
      "status": "COMPLETED",
      "payment_method": "BANK_TRANSFER",
      "transaction_id": "REP123456",
      "completed_at": "2024-01-15T16:00:00Z",
      "created_at": "2024-01-15T15:00:00Z"
    }
  ]
}
```

#### POST /api/repayments/
**Description :** Créer un nouveau remboursement

**Corps de la requête :**
```json
{
  "investment_id": "investment-uuid",
  "amount": "2500.00",
  "currency": "EUR",
  "repayment_type": "INTEREST",
  "interest_amount": "2500.00",
  "payment_method": "BANK_TRANSFER",
  "transaction_id": "REP123456",
  "notes": "Paiement d'intérêts trimestriels"
}
```

#### GET /api/repayments/{id}/
**Description :** Détails d'un remboursement

#### PATCH /api/repayments/{id}/update_status/
**Description :** Mettre à jour le statut d'un remboursement

### 4. Gestion des échéanciers

#### GET /api/schedules/
**Description :** Liste des échéances de remboursement

**Paramètres de filtrage :**
- `investment_id` : Filtrer par investissement
- `is_paid` : Filtrer par statut de paiement
- `due_date_from` : Date d'échéance minimum
- `due_date_to` : Date d'échéance maximum

**Réponse :**
```json
{
  "count": 12,
  "results": [
    {
      "id": "schedule-uuid",
      "investment": {
        "id": "investment-uuid",
        "project_title": "Application Mobile",
        "investor_name": "Jean Dupont"
      },
      "due_date": "2024-02-15",
      "amount": "2500.00",
      "principal_amount": "2000.00",
      "interest_amount": "500.00",
      "currency": "EUR",
      "is_paid": false,
      "repayment": null,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### POST /api/schedules/
**Description :** Créer un échéancier de remboursement

**Corps de la requête :**
```json
{
  "investment_id": "investment-uuid",
  "schedule_items": [
    {
      "due_date": "2024-02-15",
      "amount": "2500.00",
      "principal_amount": "2000.00",
      "interest_amount": "500.00"
    },
    {
      "due_date": "2024-03-15",
      "amount": "2500.00",
      "principal_amount": "2000.00",
      "interest_amount": "500.00"
    }
  ]
}
```

#### POST /api/schedules/generate_loan_schedule/
**Description :** Générer automatiquement un échéancier pour un prêt

**Corps de la requête :**
```json
{
  "investment_id": "investment-uuid",
  "start_date": "2024-02-01",
  "payment_frequency_months": 1
}
```

#### POST /api/schedules/{id}/link_repayment/
**Description :** Lier un remboursement à une échéance

**Corps de la requête :**
```json
{
  "repayment_id": "repayment-uuid"
}
```

### 5. URLs imbriquées

Le système supporte également des URLs imbriquées pour une navigation plus intuitive :

- `/api/investments/{investment_id}/payments/` : Paiements d'un investissement
- `/api/investments/{investment_id}/repayments/` : Remboursements d'un investissement
- `/api/investments/{investment_id}/schedules/` : Échéancier d'un investissement

## Fonctionnalités avancées

### 1. Gestion des devises

Le système supporte plusieurs devises avec conversion automatique :
- Stockage du montant et de la devise d'origine
- Conversion pour l'affichage selon les préférences utilisateur
- Support des principales devises (EUR, USD, GBP, CAD, CHF)

### 2. Calculs automatiques

#### Pour les investissements en actions (EQUITY) :
- Calcul du pourcentage de participation
- Validation des limites de dilution

#### Pour les prêts (LOAN) :
- Génération automatique d'échéanciers
- Calcul des intérêts composés
- Gestion des paiements partiels

### 3. Workflow d'approbation

1. **Création** : L'investisseur crée une demande (statut PENDING)
2. **Évaluation** : Le créateur du projet examine la demande
3. **Approbation/Rejet** : Décision du créateur avec commentaire
4. **Paiement** : Si approuvé, l'investisseur effectue le paiement
5. **Finalisation** : Statut COMPLETED une fois le paiement reçu

### 4. Historique et traçabilité

- Enregistrement automatique de tous les changements de statut
- Commentaires explicatifs pour chaque transition
- Horodatage précis de toutes les actions

## Signaux Django automatiques

### Signaux configurés

1. **post_save Investment** : Création d'entrée d'historique initiale
2. **pre_save Investment** : Mise à jour des timestamps (approved_at, completed_at)
3. **post_save InvestmentPayment** : Mise à jour du statut d'investissement si paiement complet
4. **post_save Repayment** : Mise à jour de l'échéancier si remboursement complété

## Gestion des permissions

### Permissions par endpoint

- **Investissements** : `IsAuthenticated + IsInvestorOrProjectCreator`
  - Investisseurs : Accès à leurs propres investissements
  - Créateurs : Accès aux investissements de leurs projets
  - Admins : Accès complet

- **Paiements** : Même logique que les investissements
- **Remboursements** : Accès pour payeur et bénéficiaire
- **Échéanciers** : Accès pour investisseur et créateur du projet

### Sécurité

- Validation stricte des montants et devises
- Vérification des permissions à chaque action
- Logs détaillés de toutes les transactions
- Protection contre les modifications non autorisées

## Intégration Frontend (Flutter/Dart)

### Service d'investissement

```dart
class InvestmentService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Récupérer les investissements
  static Future<List<Investment>> getInvestments({
    String? projectId,
    String? status,
    String? investmentType,
    int page = 1
  }) async {
    final queryParams = <String, String>{
      'page': page.toString(),
      if (projectId != null) 'project_id': projectId,
      if (status != null) 'status': status,
      if (investmentType != null) 'investment_type': investmentType,
    };
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/investments/').replace(
        queryParameters: queryParams
      ),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => Investment.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement investissements');
  }
  
  // Créer un investissement
  static Future<Investment> createInvestment({
    required String projectId,
    required double amount,
    required String currency,
    required String investmentType,
    double? equityPercentage,
    double? interestRate,
    int? termMonths,
    String? description,
  }) async {
    final body = <String, dynamic>{
      'project_id': projectId,
      'amount': amount.toStringAsFixed(2),
      'currency': currency,
      'investment_type': investmentType,
      if (equityPercentage != null) 'equity_percentage': equityPercentage.toStringAsFixed(2),
      if (interestRate != null) 'interest_rate': interestRate.toStringAsFixed(2),
      if (termMonths != null) 'term_months': termMonths,
      if (description != null) 'description': description,
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/api/investments/'),
      headers: await getAuthHeaders(),
      body: json.encode(body),
    );
    
    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      return Investment.fromJson(data);
    }
    throw Exception('Erreur création investissement');
  }
  
  // Mettre à jour le statut
  static Future<Investment> updateInvestmentStatus(
    String investmentId,
    String status, {
    String? comment,
  }) async {
    final body = <String, dynamic>{
      'status': status,
      if (comment != null) 'comment': comment,
    };
    
    final response = await http.patch(
      Uri.parse('$baseUrl/api/investments/$investmentId/update_status/'),
      headers: await getAuthHeaders(),
      body: json.encode(body),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return Investment.fromJson(data);
    }
    throw Exception('Erreur mise à jour statut');
  }
  
  // Créer un paiement
  static Future<InvestmentPayment> createPayment({
    required String investmentId,
    required double amount,
    required String currency,
    required String paymentMethod,
    String? transactionId,
    Map<String, dynamic>? paymentDetails,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'amount': amount.toStringAsFixed(2),
      'currency': currency,
      'payment_method': paymentMethod,
      if (transactionId != null) 'transaction_id': transactionId,
      if (paymentDetails != null) 'payment_details': paymentDetails,
      if (notes != null) 'notes': notes,
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/api/investments/$investmentId/create_payment/'),
      headers: await getAuthHeaders(),
      body: json.encode(body),
    );
    
    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      return InvestmentPayment.fromJson(data);
    }
    throw Exception('Erreur création paiement');
  }
  
  // Obtenir les statistiques
  static Future<InvestmentStats> getUserStats() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/investments/stats/'),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return InvestmentStats.fromJson(data);
    }
    throw Exception('Erreur chargement statistiques');
  }
}

class RepaymentService {
  static const String baseUrl = 'https://api.venturelink.com';
  
  // Récupérer les remboursements
  static Future<List<Repayment>> getRepayments({
    String? investmentId,
    String? status,
    String? repaymentType,
    int page = 1
  }) async {
    final queryParams = <String, String>{
      'page': page.toString(),
      if (investmentId != null) 'investment_id': investmentId,
      if (status != null) 'status': status,
      if (repaymentType != null) 'repayment_type': repaymentType,
    };
    
    final response = await http.get(
      Uri.parse('$baseUrl/api/repayments/').replace(
        queryParameters: queryParams
      ),
      headers: await getAuthHeaders(),
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => Repayment.fromJson(json))
          .toList();
    }
    throw Exception('Erreur chargement remboursements');
  }
  
  // Créer un remboursement
  static Future<Repayment> createRepayment({
    required String investmentId,
    required double amount,
    required String currency,
    required String repaymentType,
    double? principalAmount,
    double? interestAmount,
    String? paymentMethod,
    String? transactionId,
    String? notes,
  }) async {
    final body = <String, dynamic>{
      'investment_id': investmentId,
      'amount': amount.toStringAsFixed(2),
      'currency': currency,
      'repayment_type': repaymentType,
      if (principalAmount != null) 'principal_amount': principalAmount.toStringAsFixed(2),
      if (interestAmount != null) 'interest_amount': interestAmount.toStringAsFixed(2),
      if (paymentMethod != null) 'payment_method': paymentMethod,
      if (transactionId != null) 'transaction_id': transactionId,
      if (notes != null) 'notes': notes,
    };
    
    final response = await http.post(
      Uri.parse('$baseUrl/api/repayments/'),
      headers: await getAuthHeaders(),
      body: json.encode(body),
    );
    
    if (response.statusCode == 201) {
      final data = json.decode(response.body);
      return Repayment.fromJson(data);
    }
    throw Exception('Erreur création remboursement');
  }
}
```

### Modèles Dart

```dart
class Investment {
  final String id;
  final User investor;
  final Project project;
  final double amount;
  final String currency;
  final String investmentType;
  final double? equityPercentage;
  final double? interestRate;
  final int? termMonths;
  final String status;
  final String? description;
  final String? contractFile;
  final DateTime? approvedAt;
  final DateTime? completedAt;
  final DateTime createdAt;
  final DateTime updatedAt;
  
  Investment({
    required this.id,
    required this.investor,
    required this.project,
    required this.amount,
    required this.currency,
    required this.investmentType,
    this.equityPercentage,
    this.interestRate,
    this.termMonths,
    required this.status,
    this.description,
    this.contractFile,
    this.approvedAt,
    this.completedAt,
    required this.createdAt,
    required this.updatedAt,
  });
  
  factory Investment.fromJson(Map<String, dynamic> json) {
    return Investment(
      id: json['id'],
      investor: User.fromJson(json['investor']),
      project: Project.fromJson(json['project']),
      amount: double.parse(json['amount']),
      currency: json['currency'],
      investmentType: json['investment_type'],
      equityPercentage: json['equity_percentage'] != null 
          ? double.parse(json['equity_percentage']) 
          : null,
      interestRate: json['interest_rate'] != null 
          ? double.parse(json['interest_rate']) 
          : null,
      termMonths: json['term_months'],
      status: json['status'],
      description: json['description'],
      contractFile: json['contract_file'],
      approvedAt: json['approved_at'] != null 
          ? DateTime.parse(json['approved_at']) 
          : null,
      completedAt: json['completed_at'] != null 
          ? DateTime.parse(json['completed_at']) 
          : null,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
  
  bool get isPending => status == 'PENDING';
  bool get isApproved => status == 'APPROVED';
  bool get isCompleted => status == 'COMPLETED';
  bool get isRejected => status == 'REJECTED';
  bool get isCancelled => status == 'CANCELLED';
  
  bool get isEquity => investmentType == 'EQUITY';
  bool get isLoan => investmentType == 'LOAN';
  bool get isDonation => investmentType == 'DONATION';
  bool get isConvertibleNote => investmentType == 'CONVERTIBLE_NOTE';
  
  String get formattedAmount => '${amount.toStringAsFixed(2)} $currency';
  
  String get statusDisplayName {
    switch (status) {
      case 'PENDING': return 'En attente';
      case 'APPROVED': return 'Approuvé';
      case 'REJECTED': return 'Rejeté';
      case 'CANCELLED': return 'Annulé';
      case 'COMPLETED': return 'Finalisé';
      default: return status;
    }
  }
  
  String get typeDisplayName {
    switch (investmentType) {
      case 'EQUITY': return 'Actions';
      case 'LOAN': return 'Prêt';
      case 'DONATION': return 'Don';
      case 'CONVERTIBLE_NOTE': return 'Note convertible';
      default: return investmentType;
    }
  }
  
  Color get statusColor {
    switch (status) {
      case 'PENDING': return Colors.orange;
      case 'APPROVED': return Colors.blue;
      case 'COMPLETED': return Colors.green;
      case 'REJECTED': return Colors.red;
      case 'CANCELLED': return Colors.grey;
      default: return Colors.grey;
    }
  }
  
  IconData get typeIcon {
    switch (investmentType) {
      case 'EQUITY': return Icons.trending_up;
      case 'LOAN': return Icons.account_balance;
      case 'DONATION': return Icons.favorite;
      case 'CONVERTIBLE_NOTE': return Icons.transform;
      default: return Icons.attach_money;
    }
  }
}

class Repayment {
  final String id;
  final Investment investment;
  final User? paidBy;
  final User? receivedBy;
  final double amount;
  final String currency;
  final String repaymentType;
  final double? principalAmount;
  final double? interestAmount;
  final String status;
  final String paymentMethod;
  final String? transactionId;
  final String? receiptFile;
  final DateTime? completedAt;
  final DateTime createdAt;
  
  Repayment({
    required this.id,
    required this.investment,
    this.paidBy,
    this.receivedBy,
    required this.amount,
    required this.currency,
    required this.repaymentType,
    this.principalAmount,
    this.interestAmount,
    required this.status,
    required this.paymentMethod,
    this.transactionId,
    this.receiptFile,
    this.completedAt,
    required this.createdAt,
  });
  
  factory Repayment.fromJson(Map<String, dynamic> json) {
    return Repayment(
      id: json['id'],
      investment: Investment.fromJson(json['investment']),
      paidBy: json['paid_by'] != null ? User.fromJson(json['paid_by']) : null,
      receivedBy: json['received_by'] != null ? User.fromJson(json['received_by']) : null,
      amount: double.parse(json['amount']),
      currency: json['currency'],
      repaymentType: json['repayment_type'],
      principalAmount: json['principal_amount'] != null 
          ? double.parse(json['principal_amount']) 
          : null,
      interestAmount: json['interest_amount'] != null 
          ? double.parse(json['interest_amount']) 
          : null,
      status: json['status'],
      paymentMethod: json['payment_method'],
      transactionId: json['transaction_id'],
      receiptFile: json['receipt_file'],
      completedAt: json['completed_at'] != null 
          ? DateTime.parse(json['completed_at']) 
          : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
  
  bool get isPending => status == 'PENDING';
  bool get isProcessing => status == 'PROCESSING';
  bool get isCompleted => status == 'COMPLETED';
  bool get isFailed => status == 'FAILED';
  
  String get formattedAmount => '${amount.toStringAsFixed(2)} $currency';
  
  String get typeDisplayName {
    switch (repaymentType) {
      case 'PRINCIPAL': return 'Capital';
      case 'INTEREST': return 'Intérêts';
      case 'DIVIDEND': return 'Dividende';
      case 'MIXED': return 'Mixte';
      default: return repaymentType;
    }
  }
  
  Color get statusColor {
    switch (status) {
      case 'PENDING': return Colors.orange;
      case 'PROCESSING': return Colors.blue;
      case 'COMPLETED': return Colors.green;
      case 'FAILED': return Colors.red;
      default: return Colors.grey;
    }
  }
}

class InvestmentStats {
  final double totalInvested;
  final int totalInvestments;
  final int pendingInvestments;
  final int approvedInvestments;
  final int completedInvestments;
  final Map<String, InvestmentTypeStats> byType;
  final Map<String, double> byCurrency;
  
  InvestmentStats({
    required this.totalInvested,
    required this.totalInvestments,
    required this.pendingInvestments,
    required this.approvedInvestments,
    required this.completedInvestments,
    required this.byType,
    required this.byCurrency,
  });
  
  factory InvestmentStats.fromJson(Map<String, dynamic> json) {
    return InvestmentStats(
      totalInvested: double.parse(json['total_invested']),
      totalInvestments: json['total_investments'],
      pendingInvestments: json['pending_investments'],
      approvedInvestments: json['approved_investments'],
      completedInvestments: json['completed_investments'],
      byType: (json['by_type'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, InvestmentTypeStats.fromJson(value))
      ),
      byCurrency: (json['by_currency'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, double.parse(value.toString()))
      ),
    );
  }
}

class InvestmentTypeStats {
  final int count;
  final double totalAmount;
  
  InvestmentTypeStats({
    required this.count,
    required this.totalAmount,
  });
  
  factory InvestmentTypeStats.fromJson(Map<String, dynamic> json) {
    return InvestmentTypeStats(
      count: json['count'],
      totalAmount: double.parse(json['total_amount']),
    );
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

## Support multi-devises

Le système supporte l'internationalisation monétaire avec :
- Stockage des montants dans la devise d'origine
- Conversion automatique pour l'affichage
- Support des principales devises mondiales
- Taux de change mis à jour régulièrement

## Monitoring et logs

### Logs disponibles
- Création/modification d'investissements
- Changements de statut avec historique
- Transactions de paiement
- Remboursements effectués
- Erreurs de traitement

### Métriques recommandées
- Volume d'investissements par période
- Taux d'approbation des demandes
- Montants moyens par type d'investissement
- Performance des remboursements
- Conversion des devises

## Limitations et quotas

### Limitations par défaut
- **Montant minimum** : 100 EUR (ou équivalent)
- **Montant maximum** : 1 000 000 EUR par investissement
- **Devises supportées** : EUR, USD, GBP, CAD, CHF
- **Types de fichiers** : PDF, DOC, DOCX pour les contrats
- **Taille max fichier** : 10 Mo

### Optimisations performance
- Indexation des champs de recherche fréquents
- Cache des statistiques utilisateur
- Pagination des listes d'investissements
- Compression des fichiers contractuels

---

**Documentation mise à jour le :** 2024-01-15  
**Version de l'API :** 1.0  
**Contact technique :** dev@venturelink.com