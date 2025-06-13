"""
Serializers pour les modèles d'abonnement unifiés.
"""
from rest_framework import serializers
from apps.payments.models import SubscriptionPlan, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer pour les plans d'abonnement."""
    
    # Champs calculés
    duration_months = serializers.ReadOnlyField()
    is_unlimited_projects = serializers.ReadOnlyField()
    is_unlimited_investments = serializers.ReadOnlyField()
    is_unlimited_messages = serializers.ReadOnlyField()
    
    # Prix formatés pour différentes devises
    formatted_price_eur = serializers.SerializerMethodField()
    formatted_price_xaf = serializers.SerializerMethodField()
    formatted_price_usd = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'description',
            'price_eur', 'price_xaf', 'price_usd',
            'formatted_price_eur', 'formatted_price_xaf', 'formatted_price_usd',
            'duration_days', 'duration_months',
            'features',
            'max_projects', 'max_investments', 'max_messages',
            'is_unlimited_projects', 'is_unlimited_investments', 'is_unlimited_messages',
            'ai_matching', 'priority_support', 'advanced_analytics', 'custom_branding',
            'is_active', 'is_popular', 'is_free',
            'trial_days',
            'sort_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at',
            'duration_months', 'is_unlimited_projects', 'is_unlimited_investments', 'is_unlimited_messages',
            'formatted_price_eur', 'formatted_price_xaf', 'formatted_price_usd'
        ]
    
    def get_formatted_price_eur(self, obj):
        """Prix formaté en EUR."""
        return obj.format_price('EUR')
    
    def get_formatted_price_xaf(self, obj):
        """Prix formaté en XAF."""
        return obj.format_price('XAF')
    
    def get_formatted_price_usd(self, obj):
        """Prix formaté en USD."""
        return obj.format_price('USD')


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements utilisateur."""
    
    # Informations du plan
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.CharField(write_only=True)
    
    # Champs calculés
    is_active = serializers.ReadOnlyField()
    is_in_trial = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    trial_days_remaining = serializers.ReadOnlyField()
    current_period_price = serializers.ReadOnlyField()
    formatted_current_price = serializers.ReadOnlyField()
    
    # Statut lisible
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'plan', 'plan_id',
            'status', 'status_display',
            'started_at', 'expires_at', 'trial_ends_at',
            'cancelled_at', 'suspended_at',
            'auto_renew', 'next_billing_date',
            'billing_currency',
            'last_payment_date', 'last_payment_amount',
            'is_active', 'is_in_trial', 'is_expired',
            'days_remaining', 'trial_days_remaining',
            'current_period_price', 'formatted_current_price',
            'admin_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'created_at', 'updated_at',
            'is_active', 'is_in_trial', 'is_expired',
            'days_remaining', 'trial_days_remaining',
            'current_period_price', 'formatted_current_price',
            'status_display'
        ]
    
    def create(self, validated_data):
        """Créer un nouvel abonnement utilisateur."""
        plan_id = validated_data.pop('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError({
                'plan_id': 'Plan d\'abonnement non trouvé ou inactif.'
            })
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        user = self.context['request'].user
        existing_subscription = UserSubscription.objects.filter(
            user=user,
            status__in=['ACTIVE', 'TRIAL']
        ).first()
        
        if existing_subscription:
            raise serializers.ValidationError({
                'non_field_errors': 'Vous avez déjà un abonnement actif.'
            })
        
        # Créer l'abonnement
        billing_currency = validated_data.get('billing_currency', 'EUR')
        start_trial = validated_data.get('start_trial', True)
        
        subscription = UserSubscription.create_subscription(
            user=user,
            plan=plan,
            billing_currency=billing_currency,
            start_trial=start_trial
        )
        
        return subscription


class UserSubscriptionCreateSerializer(serializers.Serializer):
    """Serializer pour créer un abonnement utilisateur."""
    
    plan_id = serializers.CharField(required=True)
    billing_currency = serializers.ChoiceField(
        choices=['EUR', 'XAF', 'USD'],
        default='EUR'
    )
    start_trial = serializers.BooleanField(default=True)
    
    def validate_plan_id(self, value):
        """Valider que le plan existe et est actif."""
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError('Plan d\'abonnement non trouvé ou inactif.')
    
    def create(self, validated_data):
        """Créer un nouvel abonnement."""
        plan = SubscriptionPlan.objects.get(id=validated_data['plan_id'])
        user = self.context['request'].user
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        existing_subscription = UserSubscription.objects.filter(
            user=user,
            status__in=['ACTIVE', 'TRIAL']
        ).first()
        
        if existing_subscription:
            raise serializers.ValidationError('Vous avez déjà un abonnement actif.')
        
        subscription = UserSubscription.create_subscription(
            user=user,
            plan=plan,
            billing_currency=validated_data['billing_currency'],
            start_trial=validated_data['start_trial']
        )
        
        return subscription


class UserSubscriptionUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour un abonnement utilisateur."""
    
    class Meta:
        model = UserSubscription
        fields = [
            'auto_renew',
            'billing_currency',
            'admin_notes'
        ]
    
    def update(self, instance, validated_data):
        """Mettre à jour l'abonnement."""
        # Seuls certains champs peuvent être modifiés
        allowed_fields = ['auto_renew', 'billing_currency', 'admin_notes']
        
        for field in allowed_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance 