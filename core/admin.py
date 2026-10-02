from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Course, Enrollment, Payment, Certificate, Exam, ExamResult, Notification,
    GalleryPhoto, Schedule, Grade, Feedback, Attendance, Allocation,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_active']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'specialization', 'profile_picture')}),
    )


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'course_type', 'duration', 'fees', 'is_active', 'created_at']
    list_filter = ['course_type', 'mode', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'progress', 'enroll_date']
    list_filter = ['status', 'enroll_date']
    search_fields = ['student__username', 'course__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'course', 'amount', 'status', 'payment_date']
    list_filter = ['status', 'method', 'payment_date']
    search_fields = ['transaction_id', 'user__username']
    readonly_fields = ['transaction_id', 'payment_date']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_id', 'student', 'course', 'grade', 'issue_date', 'is_verified']
    list_filter = ['is_verified', 'issue_date']
    search_fields = ['certificate_id', 'student__username']
    readonly_fields = ['certificate_id', 'issue_date']


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'exam_date', 'total_marks', 'is_active']
    list_filter = ['is_active', 'exam_date']
    search_fields = ['title', 'course__name']


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['student', 'exam', 'marks_obtained', 'percentage', 'grade', 'passed']
    list_filter = ['passed', 'grade', 'result_date']
    search_fields = ['student__username', 'exam__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    list_display = ['type', 'caption', 'uploaded_by', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['caption']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['course', 'instructor', 'date', 'start_time', 'location']
    list_filter = ['date']
    search_fields = ['course__name', 'instructor__username']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'marks', 'grade', 'marked_by', 'created_at']
    list_filter = ['grade', 'created_at']
    search_fields = ['student__username', 'course__name']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'given_by', 'created_at']
    search_fields = ['student__username', 'course__name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'date', 'present']
    list_filter = ['present', 'date']
    search_fields = ['student__username', 'course__name']


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'course', 'status', 'allocated_by', 'allocated_at']
    list_filter = ['status']
    search_fields = ['instructor__username', 'course__name']
