from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)
router.register(r'payments', views.PaymentViewSet)
router.register(r'certificates', views.CertificateViewSet)
router.register(r'exams', views.ExamViewSet)
router.register(r'exam-results', views.ExamResultViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'gallery', views.GalleryPhotoViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'grades', views.GradeViewSet)
router.register(r'feedback', views.FeedbackViewSet)
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'allocations', views.AllocationViewSet)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', views.register_view, name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/user/', views.current_user_view, name='current-user'),
    path('profile/', views.profile_view, name='profile'),
    
    # NEW: CSRF token endpoint
    path('auth/csrf/', views.get_csrf_token, name='csrf-token'),
    
    # NEW: Health check endpoint
    path('health/', views.health_check, name='health-check'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),

    # User directory (CEO-only, backs the Export Center)
    path('users/', views.user_directory, name='user-directory'),
    
    # Include all router URLs
    path('', include(router.urls)),
]