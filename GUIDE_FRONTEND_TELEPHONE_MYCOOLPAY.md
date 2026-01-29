# Guide Frontend - Intégration Numéro de Téléphone My-CoolPay

## 🎯 Objectif
Modifier le frontend pour demander le numéro de téléphone de l'utilisateur lors de la création d'un abonnement et l'envoyer à l'API backend.

## 🔧 Modifications API Backend (✅ Déjà fait)

### Nouvel Endpoint
```http
POST /api/v1/payments/subscription/create/
Content-Type: application/json
Authorization: Bearer <firebase_token>

{
  "plan_id": "uuid-du-plan",
  "phone_number": "+237699999999"
}
```

### Validation Backend
- `plan_id` : Obligatoire (UUID du plan d'abonnement)
- `phone_number` : Obligatoire (format international recommandé)
- Validation automatique : minimum 9 chiffres
- Préfixe Cameroun ajouté automatiquement si pas de préfixe international

## 📱 Implémentation Frontend

### 1. **Interface TypeScript/JavaScript**

#### Interfaces de Données
```typescript
// Types pour l'API
interface CreateSubscriptionRequest {
  plan_id: string;
  phone_number: string;
}

interface CreateSubscriptionResponse {
  success: boolean;
  message: string;
  payment_data: {
    payment_id: string;
    payment_url: string;
    transaction_ref: string;
  };
}

interface PhoneNumberValidation {
  isValid: boolean;
  message?: string;
  formatted?: string;
}
```

#### Validation Numéro de Téléphone
```typescript
// Validation côté frontend
const validatePhoneNumber = (phone: string): PhoneNumberValidation => {
  // Nettoyer le numéro
  const cleaned = phone.replace(/[\s\-\(\)]/g, '');
  
  // Vérifier la longueur minimum
  const digitsOnly = cleaned.replace(/\+/g, '');
  if (digitsOnly.length < 9) {
    return {
      isValid: false,
      message: 'Le numéro doit contenir au moins 9 chiffres'
    };
  }
  
  // Vérifier le format
  const phoneRegex = /^\+?[1-9]\d{8,14}$/;
  if (!phoneRegex.test(cleaned)) {
    return {
      isValid: false,
      message: 'Format de numéro invalide'
    };
  }
  
  // Formater le numéro
  let formatted = cleaned;
  if (!formatted.startsWith('+')) {
    // Ajouter le préfixe Cameroun par défaut
    formatted = `+237${formatted}`;
  }
  
  return {
    isValid: true,
    formatted: formatted
  };
};
```

### 2. **Exemple React**
```typescript
import React, { useState } from 'react';

const SubscriptionForm: React.FC<{plan: any}> = ({ plan }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneError, setPhoneError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation finale
    const validation = validatePhoneNumber(phoneNumber);
    if (!validation.isValid) {
      setPhoneError(validation.message || '');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/payments/subscription/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: JSON.stringify({
          plan_id: plan.id,
          phone_number: validation.formatted!
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Rediriger vers My-CoolPay
        window.location.href = data.payment_data.payment_url;
      } else {
        setPhoneError(data.message);
      }
    } catch (error) {
      setPhoneError('Erreur lors de la création de l\'abonnement');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <h3>{plan.name}</h3>
        <p>{plan.price_xaf} FCFA / {plan.billing_cycle}</p>
      </div>

      <div>
        <label htmlFor="phone">Numéro de téléphone *</label>
        <input
          id="phone"
          type="tel"
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          placeholder="+237699999999"
          required
        />
        {phoneError && <span className="error">{phoneError}</span>}
        <small>Format international recommandé (ex: +237699999999)</small>
      </div>

      <button type="submit" disabled={isLoading || !phoneNumber}>
        {isLoading ? 'Création...' : `Payer ${plan.price_xaf} FCFA`}
      </button>
    </form>
  );
};
```

### 3. **Exemple Vue.js**
```vue
<template>
  <form @submit.prevent="handleSubmit">
    <div class="plan-info">
      <h3>{{ plan.name }}</h3>
      <p>{{ plan.price_xaf }} FCFA / {{ plan.billing_cycle }}</p>
    </div>

    <div class="form-group">
      <label for="phone">Numéro de téléphone *</label>
      <input
        id="phone"
        v-model="phoneNumber"
        type="tel"
        placeholder="+237699999999"
        required
      />
      <span v-if="phoneError" class="error">{{ phoneError }}</span>
      <small>Format international recommandé (ex: +237699999999)</small>
    </div>

    <button type="submit" :disabled="isLoading || !phoneNumber">
      {{ isLoading ? 'Création...' : `Payer ${plan.price_xaf} FCFA` }}
    </button>
  </form>
</template>

<script>
export default {
  props: ['plan'],
  data() {
    return {
      phoneNumber: '',
      phoneError: '',
      isLoading: false
    };
  },
  methods: {
    async handleSubmit() {
      const validation = this.validatePhoneNumber(this.phoneNumber);
      if (!validation.isValid) {
        this.phoneError = validation.message;
        return;
      }

      this.isLoading = true;
      
      try {
        const response = await this.$http.post('/api/v1/payments/subscription/create/', {
          plan_id: this.plan.id,
          phone_number: validation.formatted
        });
        
        if (response.data.success) {
          window.location.href = response.data.payment_data.payment_url;
        }
      } catch (error) {
        this.phoneError = 'Erreur lors de la création';
      } finally {
        this.isLoading = false;
      }
    },
    
    validatePhoneNumber(phone) {
      // Même logique de validation
    }
  }
};
</script>
```

### 4. **Exemple Flutter/Dart**
```dart
class SubscriptionForm extends StatefulWidget {
  final SubscriptionPlan plan;
  const SubscriptionForm({Key? key, required this.plan}) : super(key: key);

  @override
  _SubscriptionFormState createState() => _SubscriptionFormState();
}

class _SubscriptionFormState extends State<SubscriptionForm> {
  final _phoneController = TextEditingController();
  bool _isLoading = false;

  Future<void> _handleSubmit() async {
    String phone = _phoneController.text.trim();
    if (phone.isEmpty) return;

    if (!phone.startsWith('+')) {
      phone = '+237$phone';
    }

    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/v1/payments/subscription/create/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $firebaseToken',
        },
        body: jsonEncode({
          'plan_id': widget.plan.id,
          'phone_number': phone,
        }),
      );

      final data = jsonDecode(response.body);
      
      if (data['success']) {
        await launch(data['payment_data']['payment_url']);
      }
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              children: [
                Text(widget.plan.name, style: TextStyle(fontSize: 18)),
                Text('${widget.plan.priceXaf} FCFA / ${widget.plan.billingCycle}'),
              ],
            ),
          ),
        ),
        
        TextField(
          controller: _phoneController,
          decoration: InputDecoration(
            labelText: 'Numéro de téléphone *',
            hintText: '+237699999999',
          ),
          keyboardType: TextInputType.phone,
        ),
        
        ElevatedButton(
          onPressed: _isLoading ? null : _handleSubmit,
          child: _isLoading 
              ? CircularProgressIndicator()
              : Text('Payer ${widget.plan.priceXaf} FCFA'),
        ),
      ],
    );
  }
}
```

## ✅ Points Clés à Retenir

### 1. **Validation Frontend Obligatoire**
- Vérifier que le numéro contient au moins 9 chiffres
- Ajouter le préfixe +237 si manquant
- Afficher des messages d'erreur clairs

### 2. **Gestion des Erreurs**
- Erreur si `phone_number` manquant → "Numéro de téléphone requis"
- Erreur si `plan_id` manquant → "Plan requis"
- Erreur My-CoolPay → Afficher le message d'erreur de l'API

### 3. **UX Recommandée**
- Placeholder avec exemple : `+237699999999`
- Aide textuelle : "Format international recommandé"
- Validation en temps réel (optionnel)
- Bouton désactivé si champ vide

### 4. **Redirection My-CoolPay**
```javascript
// Après succès de l'API
if (response.success) {
  window.location.href = response.payment_data.payment_url;
}
```

## 🧪 Test Frontend
```bash
# Cas de test
1. Numéro valide : "+237699999999" → ✅ Succès
2. Numéro sans préfixe : "699999999" → ✅ Ajout auto +237
3. Numéro trop court : "123" → ❌ Erreur validation
4. Champ vide → ❌ Erreur validation
```

**Le backend est prêt ! Il ne reste plus qu'à implémenter le formulaire frontend avec ces spécifications.** 