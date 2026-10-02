from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import login, logout
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.http import JsonResponse
from asgiref.sync import async_to_sync
from .models import (
    User, Course, Enrollment, Payment, Certificate, Exam, ExamResult, Notification,
    GalleryPhoto, Schedule, Grade, Feedback, Attendance, Allocation,
)
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, CourseSerializer,
    EnrollmentSerializer, PaymentSerializer, CertificateSerializer,
    ExamSerializer, ExamResultSerializer, NotificationSerializer,
    GalleryPhotoSerializer, ScheduleSerializer, GradeSerializer,
    FeedbackSerializer, AttendanceSerializer, AllocationSerializer,
    UserDirectorySerializer,
)
from .permissions import IsCEO, IsInstructor, IsStudent
from .consumers import send_notification_to_user
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserProfileUpdateSerializer


def notify_user(user, title, message, notification_type='info', link=''):
    """Create a Notification row and push it live over the ws/notifications/
    socket to that user's group (see core/consumers.py). Used across the app
    any time an action should alert a specific user in real time."""
    notification = Notification.objects.create(
        user=user, title=title, message=message,
        notification_type=notification_type, link=link,
    )
    try:
        async_to_sync(send_notification_to_user)(user.id, {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'link': notification.link,
            'created_at': notification.created_at.isoformat(),
        })
    except Exception:
        # Channel layer may be unavailable (e.g. Redis down) — the DB
        # notification still exists and will show up on next poll.
        pass
    return notification




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
        notify_user(
            self.request.user, 'Enrollment Successful',
            f'You have been enrolled in {serializer.instance.course.name}',
            'success'
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
        notify_user(
            self.request.user, 'Payment Successful',
            f'Payment of ₹{payment.amount} completed successfully',
            'success'
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

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        certificate = serializer.save()
        notify_user(
            certificate.student, 'Certificate Issued',
            f'Your certificate for {certificate.course.name} is ready to download.',
            'success'
        )
    
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


# Gallery ViewSet (MoU Gallery + Clinical Research Gallery)
class GalleryPhotoViewSet(viewsets.ModelViewSet):
    """Gallery Photo CRUD Operations — public read, CEO-only upload/delete."""
    queryset = GalleryPhoto.objects.all()
    serializer_class = GalleryPhotoSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCEO]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        qs = self.queryset
        gallery_type = self.request.query_params.get('type')
        if gallery_type:
            qs = qs.filter(type=gallery_type)
        return qs

    def get_serializer_context(self):
        return {'request': self.request}

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


# Schedule ViewSet (specialist course scheduling / calendars)
class ScheduleViewSet(viewsets.ModelViewSet):
    """Schedule CRUD Operations"""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(course__enrollments__student=user).distinct()
        if user.role == 'instructor':
            return self.queryset.filter(instructor=user)
        return self.queryset.all()

    def perform_create(self, serializer):
        instructor = serializer.validated_data.get('instructor', self.request.user)
        serializer.save(instructor=instructor)


# Grade ViewSet (specialist marking / gradebook)
class GradeViewSet(viewsets.ModelViewSet):
    """Grade CRUD Operations"""
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(student=user)
        if user.role == 'instructor':
            return self.queryset.filter(course__schedules__instructor=user).distinct()
        return self.queryset.all()

    def perform_create(self, serializer):
        grade = serializer.save(marked_by=self.request.user)
        notify_user(
            grade.student, 'New Grade Posted',
            f'{grade.course.name}: {grade.grade or grade.marks}',
            'info'
        )


# Feedback ViewSet (specialist feedback to students)
class FeedbackViewSet(viewsets.ModelViewSet):
    """Feedback CRUD Operations"""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return self.queryset.filter(student=user)
        if user.role == 'instructor':
            return self.queryset.filter(course__schedules__instructor=user).distinct()
        return self.queryset.all()

    def perform_create(self, serializer):
        feedback = serializer.save(given_by=self.request.user)
        notify_user(
            feedback.student, 'New Feedback Received',
            f'{feedback.course.name}: {feedback.message[:80]}',
            'info'
        )


# Attendance ViewSet
class AttendanceViewSet(viewsets.ModelViewSet):
    """Attendance CRUD Operations"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        qs = self.queryset
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        if user.role == 'student':
            return qs.filter(student=user)
        if user.role == 'instructor':
            return qs.filter(course__schedules__instructor=user).distinct()
        return qs

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)


# Allocation ViewSet (CEO assigns specialists to courses)
class AllocationViewSet(viewsets.ModelViewSet):
    """Allocation CRUD Operations — CEO-only write, Instructor/CEO read."""
    queryset = Allocation.objects.all()
    serializer_class = AllocationSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsCEO]
        else:
            permission_classes = [IsAuthenticated, IsInstructor | IsCEO]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'instructor':
            return self.queryset.filter(instructor=user)
        return self.queryset.all()

    def perform_create(self, serializer):
        allocation = serializer.save(allocated_by=self.request.user)
        notify_user(
            allocation.instructor, 'New Course Allocation',
            f'You have been allocated to {allocation.course.name}.',
            'info'
        )


# User Directory (CEO-only — backs the Export Center's Enrolled Students /
# Specialist directory exports)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCEO])
def user_directory(request):
    """List users, optionally filtered by ?role=student|instructor|ceo"""
    qs = User.objects.all().order_by('-created_at')
    role = request.query_params.get('role')
    if role:
        qs = qs.filter(role=role)
    serializer = UserDirectorySerializer(qs, many=True)
    return Response(serializer.data)


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
            'total_certificates': Certificate.objects.count(),
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
    