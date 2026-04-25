"""
Views for the DRC Asset Lending Management System.
"""
import uuid, json
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User, Direction, Department, SubDepartment, Equipment, Movement
from .serializers import (
    UserSerializer, UserCreateSerializer, UserMinimalSerializer,
    DirectionSerializer, DepartmentSerializer, SubDepartmentSerializer,
    EquipmentSerializer, EquipmentMinimalSerializer,
    MovementSerializer, MovementCreateSerializer,
)

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'ADMIN'

# ── Page Views ──
def login_page(request):
    if request.user.is_authenticated:
        return redirect('/situation/')
    return render(request, 'login.html')

def administration_page(request):
    if not request.user.is_authenticated: return redirect('/login/')
    if request.user.role != 'ADMIN': return redirect('/situation/')
    return render(request, 'administration.html')

def mouvement_page(request):
    if not request.user.is_authenticated: return redirect('/login/')
    return render(request, 'mouvement.html')

def situation_page(request):
    if not request.user.is_authenticated: return redirect('/login/')
    return render(request, 'situation.html')

def verify_email_page(request):
    return render(request, 'verify_email.html')

# ── Auth API ──
@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    try: data = json.loads(request.body)
    except: return JsonResponse({'error': 'Invalid JSON'}, status=400)
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if not email or not password:
        return JsonResponse({'error': 'Email et mot de passe requis.'}, status=400)
    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({'error': 'Identifiants invalides.'}, status=401)
    if not user.is_active:
        return JsonResponse({'error': 'Compte désactivé.'}, status=403)
    if not user.email_verified:
        return JsonResponse({'error': 'email_not_verified', 'message': 'Vérifiez votre email.', 'user_id': str(user.id)}, status=403)
    login(request, user)
    return JsonResponse({'success': True, 'user': {'id': str(user.id), 'name': user.name, 'email': user.email, 'role': user.role}})

@csrf_exempt
def api_logout(request):
    logout(request)
    return JsonResponse({'success': True})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_me(request):
    u = request.user
    return Response({'id': str(u.id), 'name': u.name, 'email': u.email, 'role': u.role, 'email_verified': u.email_verified})

# ── Email Verification ──
@csrf_exempt
@require_http_methods(["POST"])
def api_send_verification(request):
    try: data = json.loads(request.body)
    except: return JsonResponse({'error': 'Invalid JSON'}, status=400)
    user_id = data.get('user_id')
    try: user = User.objects.get(id=user_id)
    except: return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)
    token = uuid.uuid4().hex[:32]
    user.verification_token = token
    user.save(update_fields=['verification_token'])
    verify_url = f"{request.scheme}://{request.get_host()}/verify-email/?token={token}"
    send_mail('DRC - Vérification email', f'Bonjour {user.name},\n\nLien: {verify_url}', 'noreply@dominionrc.com', [user.email], fail_silently=True)
    return JsonResponse({'success': True, 'message': f'Email envoyé à {user.email}', 'token': token})

@csrf_exempt
@require_http_methods(["POST"])
def api_verify_email(request):
    try: data = json.loads(request.body)
    except: return JsonResponse({'error': 'Invalid JSON'}, status=400)
    token = data.get('token', '').strip()
    if not token: return JsonResponse({'error': 'Token requis'}, status=400)
    try: user = User.objects.get(verification_token=token)
    except: return JsonResponse({'error': 'Token invalide.'}, status=400)
    user.email_verified = True
    user.verification_token = ''
    user.save(update_fields=['email_verified', 'verification_token'])
    return JsonResponse({'success': True, 'message': 'Email vérifié avec succès.'})

# ── User Management ──
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_users(request):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Accès refusé'}, status=403)
    if request.method == 'GET':
        return Response(UserSerializer(User.objects.all(), many=True).data)
    s = UserCreateSerializer(data=request.data)
    if s.is_valid():
        return Response(UserSerializer(s.save()).data, status=201)
    return Response(s.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_user_detail(request, pk):
    if request.user.role != 'ADMIN':
        return Response({'error': 'Accès refusé'}, status=403)
    try: user = User.objects.get(pk=pk)
    except: return Response({'error': 'Non trouvé'}, status=404)
    if request.method == 'GET':
        return Response(UserSerializer(user).data)
    if request.method == 'PUT':
        s = UserSerializer(user, data=request.data, partial=True)
        if s.is_valid(): s.save(); return Response(s.data)
        return Response(s.errors, status=400)
    user.is_active = False; user.save(update_fields=['is_active'])
    return Response({'success': True})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_users_list(request):
    return Response(UserMinimalSerializer(User.objects.filter(is_active=True), many=True).data)

# ── Organization ──
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_directions(request):
    if request.method == 'GET':
        return Response(DirectionSerializer(Direction.objects.all(), many=True).data)
    if request.user.role != 'ADMIN': return Response({'error': 'Accès refusé'}, status=403)
    s = DirectionSerializer(data=request.data)
    if s.is_valid(): s.save(); return Response(s.data, status=201)
    return Response(s.errors, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_departments(request):
    if request.method == 'GET':
        qs = Department.objects.select_related('direction').all()
        d = request.GET.get('direction_id')
        if d: qs = qs.filter(direction_id=d)
        return Response(DepartmentSerializer(qs, many=True).data)
    if request.user.role != 'ADMIN': return Response({'error': 'Accès refusé'}, status=403)
    s = DepartmentSerializer(data=request.data)
    if s.is_valid(): s.save(); return Response(s.data, status=201)
    return Response(s.errors, status=400)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_subdepartments(request):
    if request.method == 'GET':
        qs = SubDepartment.objects.select_related('department').all()
        d = request.GET.get('department_id')
        if d: qs = qs.filter(department_id=d)
        return Response(SubDepartmentSerializer(qs, many=True).data)
    if request.user.role != 'ADMIN': return Response({'error': 'Accès refusé'}, status=403)
    s = SubDepartmentSerializer(data=request.data)
    if s.is_valid(): s.save(); return Response(s.data, status=201)
    return Response(s.errors, status=400)

# ── Equipment ──
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_equipment(request):
    if request.method == 'GET':
        return Response(EquipmentSerializer(Equipment.objects.all(), many=True).data)
    if request.user.role not in ['ADMIN', 'MANAGER']:
        return Response({'error': 'Accès refusé'}, status=403)
    s = EquipmentSerializer(data=request.data)
    if s.is_valid(): s.save(); return Response(s.data, status=201)
    return Response(s.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def api_equipment_detail(request, pk):
    try: eq = Equipment.objects.get(pk=pk)
    except: return Response({'error': 'Non trouvé'}, status=404)
    if request.method == 'GET': return Response(EquipmentSerializer(eq).data)
    if request.user.role not in ['ADMIN', 'MANAGER']:
        return Response({'error': 'Accès refusé'}, status=403)
    if request.method == 'PUT':
        s = EquipmentSerializer(eq, data=request.data, partial=True)
        if s.is_valid(): s.save(); return Response(s.data)
        return Response(s.errors, status=400)
    if eq.movements.exists():
        return Response({'error': 'Mouvements existants.'}, status=400)
    eq.delete(); return Response({'success': True})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_equipment_list(request):
    return Response(EquipmentMinimalSerializer(Equipment.objects.all(), many=True).data)

# ── Movements ──
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def api_movements(request):
    if request.method == 'GET':
        qs = Movement.objects.select_related('completed_by', 'assigned_to', 'equipment', 'direction', 'department').all()
        at = request.GET.get('action_type')
        if at: qs = qs.filter(action_type=at)
        eid = request.GET.get('equipment_id')
        if eid: qs = qs.filter(equipment_id=eid)
        return Response(MovementSerializer(qs[:200], many=True).data)
    s = MovementCreateSerializer(data=request.data, context={'request': request})
    if s.is_valid():
        mv = s.save()
        return Response(MovementSerializer(mv).data, status=201)
    return Response(s.errors, status=400)

# ── Stock ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_stock(request):
    data = []
    for eq in Equipment.objects.all():
        data.append({'equipment_id': eq.id, 'equipment_name': eq.name, 'internal_id': eq.internal_id, 'model': eq.model, 'condition': eq.get_condition_display(), 'current_stock': eq.current_stock})
    return Response(data)

# ── Active Loans ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_loans(request):
    loans = Movement.objects.filter(action_type='PRET').select_related('equipment', 'assigned_to', 'direction').values('equipment__id', 'equipment__name', 'equipment__internal_id', 'assigned_to__name', 'assigned_to__id', 'direction__name').annotate(total_loaned=Sum('quantity'))
    result = []
    for l in loans:
        ret = Movement.objects.filter(action_type='RETOUR', equipment_id=l['equipment__id'], assigned_to_id=l['assigned_to__id']).aggregate(t=Sum('quantity'))['t'] or 0
        net = l['total_loaned'] - ret
        if net > 0:
            latest = Movement.objects.filter(action_type='PRET', equipment_id=l['equipment__id'], assigned_to_id=l['assigned_to__id']).order_by('-date').first()
            result.append({'equipment_id': l['equipment__id'], 'equipment_name': l['equipment__name'], 'internal_id': l['equipment__internal_id'], 'assigned_to_name': l['assigned_to__name'], 'assigned_to_id': str(l['assigned_to__id']), 'quantity_loaned': net, 'loan_date': latest.date if latest else None, 'direction_name': l['direction__name']})
    return Response(result)

# ── History ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_history(request):
    qs = Movement.objects.select_related('completed_by', 'assigned_to', 'equipment', 'direction', 'department').all()
    at = request.GET.get('action_type')
    if at: qs = qs.filter(action_type=at)
    eid = request.GET.get('equipment_id')
    if eid: qs = qs.filter(equipment_id=eid)
    df = request.GET.get('date_from')
    if df: qs = qs.filter(date__gte=df)
    dt = request.GET.get('date_to')
    if dt: qs = qs.filter(date__lte=dt)
    summary = qs.aggregate(e=Sum('quantity', filter=Q(action_type='ENTREE')), s=Sum('quantity', filter=Q(action_type='SORTIE')), p=Sum('quantity', filter=Q(action_type='PRET')), r=Sum('quantity', filter=Q(action_type='RETOUR')))
    return Response({'movements': MovementSerializer(qs[:500], many=True).data, 'summary': {'total_entrees': summary['e'] or 0, 'total_sorties': summary['s'] or 0, 'total_prets': summary['p'] or 0, 'total_retours': summary['r'] or 0}, 'count': qs.count()})

# ── Dashboard Stats ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard_stats(request):
    loans = Movement.objects.filter(action_type='PRET').values('equipment_id', 'assigned_to_id').annotate(loaned=Sum('quantity'))
    active = 0
    for l in loans:
        ret = Movement.objects.filter(action_type='RETOUR', equipment_id=l['equipment_id'], assigned_to_id=l['assigned_to_id']).aggregate(t=Sum('quantity'))['t'] or 0
        if l['loaned'] - ret > 0: active += 1
    return Response({'total_equipment': Equipment.objects.count(), 'total_movements': Movement.objects.count(), 'active_loans': active, 'total_users': User.objects.filter(is_active=True).count()})
