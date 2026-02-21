from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import login, logout
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.http import JsonResponse
from .models import User, Course, Enrollment, Payment, Certificate, Exam, ExamResult, Notification
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, CourseSerializer,
    EnrollmentSerializer, PaymentSerializer, CertificateSerializer,
    ExamSerializer, ExamResultSerializer, NotificationSerializer
)
from .permissions import IsCEO, IsInstructor, IsStudent
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserProfileUpdateSerializer




# CSRF Token Endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token(request):
    """Endpoint to ensure CSRF cookie is set"""
    return Response({'detail': 'CSRF cookie set'}, status=status.HTTP_200_OK)


# Health Check Endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def health_check(request):
    """Health check endpoint that sets CSRF cookie"""
    return Response({
        'status': 'healthy',
        'csrf_set': 'csrftoken' in request.COOKIES
    })


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def register_view(request):
    """User Registration"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def login_view(request):
    """User Login"""
    # Manually set CSRF token if not present
    if not request.META.get('CSRF_COOKIE'):
        get_token(request)
    
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """User Logout"""
    logout(request)
    response = Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    # Clear CSRF cookie on logout
    response.delete_cookie('csrftoken')
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """Get Current User"""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# Course ViewSet
class CourseViewSet(viewsets.ModelViewSet):
    """Course CRUD Operations"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCEO]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search courses"""
        query = request.query_params.get('q', '')
        course_type = request.query_params.get('type', '')
        
        courses = self.queryset.filter(is_active=True)
        
        if query:
            courses = courses.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if course_type:
            courses = courses.filter(course_type=course_type)
        
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)


# Enrollment ViewSet
class EnrollmentViewSet(viewsets.ModelViewSet):
    """Enrollment CRUD Operations"""
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(student=user)
        elif user.role == 'instructor':
            return self.queryset.all()
        elif user.role == 'ceo':
            return self.queryset.all()
        return self.queryset.none()
    
    def perform_create(self, serializer):
        serializer.save(student=self.request.user)
        
        # Create notification
        Notification.objects.create(
            user=self.request.user,
            title='Enrollment Successful',
            message=f'You have been enrolled in {serializer.instance.course.name}',
            notification_type='success'
        )
    
    @action(detail=True, methods=['patch'])
    def update_progress(self, request, pk=None):
        """Update enrollment progress"""
        enrollment = self.get_object()
        progress = request.data.get('progress', enrollment.progress)
        enrollment.progress = min(100, max(0, int(progress)))
        enrollment.save()
        
        return Response(self.get_serializer(enrollment).data)


# Payment ViewSet
class PaymentViewSet(viewsets.ModelViewSet):
    """Payment CRUD Operations"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(user=user)
        return self.queryset.all()
    
    def perform_create(self, serializer):
        payment = serializer.save(user=self.request.user)
        
        # Create notification
        Notification.objects.create(
            user=self.request.user,
            title='Payment Successful',
            message=f'Payment of ₹{payment.amount} completed successfully',
            notification_type='success'
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get payment statistics"""
        if request.user.role != 'ceo':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        stats = {
            'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'completed_payments': Payment.objects.filter(status='completed').count(),
            'failed_payments': Payment.objects.filter(status='failed').count(),
        }
        return Response(stats)


# Certificate ViewSet
class CertificateViewSet(viewsets.ModelViewSet):
    """Certificate CRUD Operations"""
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(student=user)
        return self.queryset.all()
    
    @action(detail=False, methods=['get'])
    def verify(self, request):
        """Verify certificate by ID"""
        cert_id = request.query_params.get('certificate_id')
        try:
            certificate = Certificate.objects.get(certificate_id=cert_id, is_verified=True)
            serializer = self.get_serializer(certificate)
            return Response(serializer.data)
        except Certificate.DoesNotExist:
            return Response({'error': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)


# Exam ViewSet
class ExamViewSet(viewsets.ModelViewSet):
    """Exam CRUD Operations"""
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# Exam Result ViewSet
class ExamResultViewSet(viewsets.ModelViewSet):
    """Exam Result CRUD Operations"""
    queryset = ExamResult.objects.all()
    serializer_class = ExamResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(student=user)
        return self.queryset.all()


# Notification ViewSet
class NotificationViewSet(viewsets.ModelViewSet):
    """Notification CRUD Operations"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(self.get_serializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get unread notification count"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


# Dashboard Statistics
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ensure_csrf_cookie
def dashboard_stats(request):
    """Get dashboard statistics based on user role"""
    user = request.user
    
    if user.role == 'student':
        stats = {
            'enrolled_courses': Enrollment.objects.filter(student=user, status='active').count(),
            'completed_courses': Enrollment.objects.filter(student=user, status='completed').count(),
            'certificates': Certificate.objects.filter(student=user).count(),
            'pending_exams': Exam.objects.filter(
                course__enrollments__student=user,
                exam_date__gte=timezone.now()
            ).count(),
        }
    elif user.role == 'instructor':
        stats = {
            'total_students': Enrollment.objects.filter(status='active').values('student').distinct().count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'scheduled_exams': Exam.objects.filter(is_active=True, exam_date__gte=timezone.now()).count(),
            'certificates_issued': Certificate.objects.count(),
        }
    elif user.role == 'ceo':
        stats = {
            'total_revenue': Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0,
            'total_students': User.objects.filter(role='student').count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'total_enrollments': Enrollment.objects.filter(status='active').count(),
        }
    else:
        stats = {}
    
    return Response(stats)


# Simple middleware to ensure CSRF cookie is set
class EnsureCSRFCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set CSRF token if not present
        if not request.META.get('CSRF_COOKIE'):
            get_token(request)
        response = self.get_response(request)
        return response

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    GET: Retrieve current user profile
    PATCH: Update user profile (partial update with nullable fields)
    """
    user = request.user
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserProfileUpdateSerializer(
            user, 
            data=request.data, 
            partial=True,  # This allows partial updates
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    