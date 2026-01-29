# subscriptions/views.py
from datetime import time, timedelta
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from django.views import View
from django.http import HttpResponse
import uuid
from django.utils import timezone
import django.db.utils

from .models import Subscription
from .services import PaymentService

class InitiateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            phone_number = request.data.get('phone_number')
            language = request.data.get('language', 'fr')
            service_type = request.data.get('service_type', 'premium')  # 'premium' ou 'coach_subscription'
            service_id = request.data.get('service_id')  # ID du coach si service_type = 'coach_subscription'
            amount = request.data.get('amount', 50)  # Montant par défaut
            
            if not phone_number:
                return Response(
                    {'error': 'Le numéro de téléphone est requis'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Variables pour stocker les informations du coach
            coach = None
            coach_name = None
            
            # Si c'est un abonnement coach, valider et récupérer les infos du coach
            if service_type == 'coach_subscription':
                if not service_id:
                    return Response(
                        {'error': 'L\'ID du coach est requis pour l\'abonnement coach'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                try:
                    from coaching.models import Coach, FXAccount, CryptoAccount
                    coach = Coach.objects.get(id=service_id)
                    coach_name = coach.user.get_full_name() or coach.user.email
                    
                    # Utiliser le prix mensuel défini par le coach
                    amount = coach.monthly_price
                    print(f"[DEBUG] Prix coach utilisé pour l'abonnement: {amount}")
                    
                    # Vérifier que le coach a au moins un compte de trading connecté
                    has_forex = FXAccount.objects.filter(coach=coach, is_active=True).exists()
                    has_crypto = CryptoAccount.objects.filter(coach=coach, is_active=True).exists()
                    
                    if not (has_forex or has_crypto):
                        return Response(
                            {'error': 'Ce coach n\'a pas encore de comptes de trading connectés'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                    # Vérifier si l'utilisateur n'est pas déjà abonné
                    from coaching.models import CoachSubscription
                    
                    # Vérifier si un abonnement existe déjà, qu'il soit actif ou non
                    existing_sub = CoachSubscription.objects.filter(
                        user=request.user,
                        coach=coach
                    ).first()
                    
                    if existing_sub:
                        # Si un abonnement existe et qu'il est encore actif et non expiré
                        if existing_sub.is_active and existing_sub.end_date > timezone.now():
                            return Response(
                                {'error': 'Vous êtes déjà abonné à ce coach'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        else:
                            # Si l'abonnement existe mais est inactif ou expiré
                            print(f"[DEBUG] Abonnement existant trouvé mais inactif ou expiré, ID: {existing_sub.id}")
                            # On le supprime pour permettre d'en créer un nouveau
                            existing_sub.delete()
                            print(f"[DEBUG] Ancien abonnement supprimé")
                        
                except Coach.DoesNotExist:
                    return Response(
                        {'error': 'Coach non trouvé'},
                        status=status.HTTP_404_NOT_FOUND
                    )

            print(f"[DEBUG] Initier le paiement pour {request.user.email}, coach_name: {coach_name}")
            try:
                # Initier le paiement avec My-CoolPay
                payment_data, transaction_ref = PaymentService.initiate_payment(
                    user=request.user,
                    phone_number=phone_number,
                    language=language,
                    amount=amount,
                    service_type=service_type,
                    coach_name=coach_name
                )
                
                print(f"[DEBUG] Paiement initié, transaction_ref: {transaction_ref}")
                print(f"[DEBUG] Payment data: {payment_data}")
                
                # Créer l'enregistrement d'abonnement approprié
                if service_type == 'coach_subscription':
                    try:
                        from coaching.models import CoachSubscription
                        print(f"[DEBUG] Création abonnement coach, coach: {coach.id}, user: {request.user.id}")
                        
                        # S'assurer que l'URL de paiement est valide
                        payment_url = payment_data.get('payment_url', '')
                        if not payment_url:
                            print(f"[WARNING] URL de paiement vide, utilisation de valeur par défaut")
                            payment_url = ''
                        
                        try:
                            subscription = CoachSubscription.objects.create(
                                user=request.user,
                                coach=coach,
                                end_date=timezone.now() + timedelta(days=30),
                                transaction_ref=transaction_ref,
                                is_active=False,  # Sera activé après paiement réussi
                                payment_url=payment_url
                            )
                            print(f"[DEBUG] Abonnement coach créé: {subscription.id}")
                        except django.db.utils.IntegrityError as db_error:
                            # Cas où la contrainte unique serait toujours violée
                            print(f"[ERROR] Erreur d'intégrité lors de la création de l'abonnement: {str(db_error)}")
                            
                            # Essayer de récupérer l'abonnement existant pour le mettre à jour
                            try:
                                existing_sub = CoachSubscription.objects.get(user=request.user, coach=coach)
                                existing_sub.transaction_ref = transaction_ref
                                existing_sub.is_active = False
                                existing_sub.end_date = timezone.now() + timedelta(days=30)
                                existing_sub.payment_url = payment_url
                                existing_sub.save()
                                subscription = existing_sub
                                print(f"[DEBUG] Abonnement existant mis à jour: {subscription.id}")
                            except Exception as inner_error:
                                print(f"[ERROR] Impossible de mettre à jour l'abonnement existant: {str(inner_error)}")
                                raise Exception(f"Erreur lors de la mise à jour de l'abonnement: {str(inner_error)}")
                        
                    except Exception as coach_sub_error:
                        import traceback
                        print(f"[ERROR] Erreur création abonnement coach: {str(coach_sub_error)}")
                        print(traceback.format_exc())
                        raise Exception(f"Erreur création abonnement coach: {str(coach_sub_error)}")
                else:
                    try:
                        # Abonnement premium standard
                        print(f"[DEBUG] Création abonnement premium standard")
                        
                        # S'assurer que l'URL de paiement est valide
                        try:
                            payment_url = payment_data.get('payment_url', '')
                        except Exception as url_error:
                            print(f"[WARNING] Erreur lors de la récupération de l'URL de paiement: {url_error}")
                            payment_url = ''
                        
                        subscription = Subscription.objects.create(
                            user=request.user,
                            transaction_ref=transaction_ref,
                            amount=amount,
                            payment_url=payment_url,
                            status='pending'
                        )
                        print(f"[DEBUG] Abonnement premium créé: {subscription.id}")
                    except Exception as sub_error:
                        import traceback
                        print(f"[ERROR] Erreur création abonnement standard: {str(sub_error)}")
                        print(traceback.format_exc())
                        raise Exception(f"Erreur création abonnement standard: {str(sub_error)}")

                return Response({
                    'payment_url': payment_data['payment_url'],
                    'transaction_ref': transaction_ref,
                    'service_type': service_type,
                    'service_id': service_id
                })
            except Exception as payment_error:
                import traceback
                print(f"[ERROR] Erreur dans le processus de paiement: {str(payment_error)}")
                print(traceback.format_exc())
                raise Exception(f"Erreur dans le processus de paiement: {str(payment_error)}")

        except Exception as e:
            import traceback
            print(f"[ERROR] Exception dans InitiateSubscriptionView: {str(e)}")
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PaymentCallbackView(View):
    def get(self, request):
        status = request.GET.get('status')
        # Page HTML simple avec un script de redirection
        html = f'''
        <html>
        <head>
            <title>Redirection...</title>
            <script>
                window.onload = function() {{
                    window.location.href = "xptrading://payment/callback?status={status}";
                }}
            </script>
        </head>
        <body>
            <p>Redirection en cours...</p>
        </body>
        </html>
        '''
        return HttpResponse(html)
    
class UpdatePremiumStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            print("=== Starting premium status update ===")
            print(f"Auth header: {request.headers.get('Authorization', 'None')[:20]}...")
            
            # Vérifier l'authentification
            if not request.user.is_authenticated:
                print("User not authenticated")
                return Response(
                    {'error': 'Authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            user = request.user
            print(f"Processing premium update for user: {user.email}, ID: {user.id}")

            # Mise à jour directe des champs
            user.is_premium = True
            user.premium_end_date = timezone.now() + timedelta(days=30)
            
            # Force save
            try:
                user.save(update_fields=['is_premium', 'premium_end_date'])
                print(f"User saved successfully. Premium: {user.is_premium}")
            except Exception as save_error:
                print(f"Error saving user: {save_error}")
                raise
            
            # Vérification de la mise à jour
            fresh_user = type(user).objects.get(pk=user.pk)
            print(f"Verification - Is Premium: {fresh_user.is_premium}")
            
            # Créer une souscription
            subscription = Subscription.objects.create(
                user=user,
                status='active',
                amount=50,
                transaction_ref=f"sub_{uuid.uuid4().hex[:10]}"
            )
            
            print(f"Subscription created: {subscription.transaction_ref}")

            return Response({
                'status': 'success',
                'user': {
                    'is_premium': user.is_premium,
                    'premium_end_date': user.premium_end_date.isoformat(),
                    'email': user.email,
                }
            })

        except Exception as e:
            print(f"Error updating premium status: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_subscription(request):
    """Initier un processus de paiement d'abonnement"""
    phone_number = request.data.get('phone_number')
    language = request.data.get('language', 'fr')
    service_type = request.data.get('service_type', 'premium')
    service_id = request.data.get('service_id')
    amount = request.data.get('amount')
    
    if not phone_number:
        return Response(
            {"error": "Phone number is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Valider montant - soit montant spécifié, soit le montant standard premium
    if not amount:
        amount = 50  # Montant par défaut pour premium
    
    # Générer une référence unique pour la transaction
    transaction_ref = f"xpt_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # Créer un enregistrement de l'abonnement
    subscription = None
    coach_name = None
    
    if service_type == 'coach_subscription' and service_id:
        try:
            from coaching.models import Coach, CoachSubscription
            coach = Coach.objects.get(id=service_id)
            coach_name = coach.user.email  # Obtenir le nom/email du coach
            
            # Utiliser le prix mensuel défini par le coach
            amount = coach.monthly_price
            print(f"[DEBUG] Prix coach utilisé pour l'abonnement: {amount}")
            
            # Vérifier que le coach a au moins un compte de trading connecté
            from coaching.models import FXAccount, CryptoAccount
            has_forex = FXAccount.objects.filter(coach=coach, is_active=True).exists()
            has_crypto = CryptoAccount.objects.filter(coach=coach, is_active=True).exists()
            
            if not (has_forex or has_crypto):
                return Response(
                    {"error": "This coach does not have any connected trading accounts yet"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Vérifier si un abonnement existe déjà
            existing_sub = CoachSubscription.objects.filter(
                user=request.user,
                coach=coach
            ).first()
            
            if existing_sub:
                # Si abonnement actif et non expiré
                if existing_sub.is_active and existing_sub.end_date > timezone.now():
                    return Response(
                        {"error": "You are already subscribed to this coach"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # Si abonnement inactif ou expiré, le supprimer
                    existing_sub.delete()
            
            # Créer l'abonnement coach (30 jours)
            try:
                subscription = CoachSubscription.objects.create(
                    user=request.user,
                    coach=coach,
                    end_date=timezone.now() + timedelta(days=30),
                    transaction_ref=transaction_ref,
                    is_active=False  # Sera activé après paiement
                )
            except django.db.utils.IntegrityError:
                # Si toujours problème de contrainte unique, mettre à jour l'abonnement existant
                existing_sub = CoachSubscription.objects.get(user=request.user, coach=coach)
                existing_sub.end_date = timezone.now() + timedelta(days=30)
                existing_sub.transaction_ref = transaction_ref
                existing_sub.is_active = False
                existing_sub.save()
                subscription = existing_sub
            
        except Coach.DoesNotExist:
            return Response(
                {"error": "Coach not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Pour un abonnement premium standard
        subscription = Subscription.objects.create(
            user=request.user,
            amount=amount,
            transaction_ref=transaction_ref,
            status='pending'
        )
    
    if not subscription:
        return Response(
            {"error": "Invalid service type or missing service ID"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Intégrer avec votre passerelle de paiement
    try:
        payment_data, tx_ref = PaymentService.initiate_payment(
            user=request.user,
            phone_number=phone_number,
            language=language,
            amount=amount,
            service_type=service_type,
            coach_name=coach_name
        )
        
        # Mettre à jour l'URL de paiement
        if hasattr(subscription, 'payment_url'):
            subscription.payment_url = payment_data['payment_url']
            subscription.save()
            
        return Response({
            "payment_url": payment_data['payment_url'],
            "transaction_ref": tx_ref,
            "service_type": service_type,  # Ajouter le type de service
            "service_id": service_id  # Ajouter l'ID du service
        })
    except Exception as e:
        # Annuler l'abonnement en cas d'erreur
        subscription.delete()
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ActivateCoachSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Activer un abonnement coach après paiement réussi"""
        try:
            transaction_ref = request.data.get('transaction_ref')
            
            if not transaction_ref:
                return Response(
                    {'error': 'La référence de transaction est requise'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Trouver l'abonnement coach par référence de transaction
            from coaching.models import CoachSubscription
            try:
                subscription = CoachSubscription.objects.get(
                    transaction_ref=transaction_ref,
                    user=request.user
                )
            except CoachSubscription.DoesNotExist:
                return Response(
                    {'error': 'Abonnement non trouvé'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Activer l'abonnement
            subscription.is_active = True
            subscription.save()

            # Mettre à jour le compteur d'abonnés du coach
            coach = subscription.coach
            coach.followers_count += 1
            coach.save()

            # Notifier le coach (optionnel)
            try:
                from notifications.models import FCMToken
                from firebase_admin import messaging
                
                coach_user = coach.user
                fcm_tokens = FCMToken.objects.filter(user_id=coach_user.id).values_list('token', flat=True)

                for token in fcm_tokens:
                    try:
                        message = messaging.Message(
                            data={
                                'type': 'new_subscriber',
                                'subscription_id': str(subscription.id),
                                'user_email': request.user.email,
                            },
                            notification=messaging.Notification(
                                title=f"Nouvel abonné !",
                                body=f"Un nouvel utilisateur s'est abonné à votre profil coach."
                            ),
                            token=token
                        )
                        
                        messaging.send(message)
                    except Exception as e:
                        print(f"Error sending notification to coach: {e}")
            except ImportError:
                # Les notifications ne sont pas configurées, continuer sans erreur
                pass

            return Response({
                'status': 'success',
                'message': 'Abonnement coach activé avec succès',
                'subscription': {
                    'id': str(subscription.id),
                    'coach_email': subscription.coach.user.email,
                    'end_date': subscription.end_date.isoformat(),
                    'is_active': subscription.is_active
                }
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )