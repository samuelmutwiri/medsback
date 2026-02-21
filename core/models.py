from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    """Custom User Model"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('ceo', 'CEO'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.role}"
    
    class Meta:
        ordering = ['-created_at']


class Course(models.Model):
    """Course Model"""
    TYPE_CHOICES = [
        ('PG', 'Postgraduate'),
        ('Certificate', 'Certificate'),
        ('Fellowship', 'Fellowship'),
        ('MS', 'Master of Science'),
    ]
    
    MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Online/Offline'),
    ]
    
    name = models.CharField(max_length=200)
    course_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    duration = models.CharField(max_length=50)
    eligibility = models.TextField()
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='hybrid')
    fees = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    syllabus = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='courses_created')
    
    def __str__(self):
        return f"{self.name} - {self.course_type}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_type', 'is_active']),
        ]


class Enrollment(models.Model):
    """Student Course Enrollment"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enroll_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress = models.IntegerField(default=0)  # Percentage 0-100
    completion_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enroll_date']
        indexes = [
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.course.name}"


class Payment(models.Model):
    """Payment Transactions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    METHOD_CHOICES = [
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
        ('cash', 'Cash'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    enrollment = models.ForeignKey(Enrollment, on_delete=models.SET_NULL, null=True, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"Payment #{self.transaction_id} - {self.user.username}"


class Certificate(models.Model):
    """Student Certificates"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    certificate_id = models.CharField(max_length=100, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    grade = models.CharField(max_length=10)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['certificate_id']),
        ]
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student.username}"


class Exam(models.Model):
    """Examination Schedule"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    exam_date = models.DateTimeField()
    duration = models.CharField(max_length=50)  # e.g., "3 hours"
    total_marks = models.IntegerField()
    passing_marks = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='exams_created')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['exam_date']
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"


class ExamResult(models.Model):
    """Student Exam Results"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_results')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=10)
    passed = models.BooleanField(default=False)
    remarks = models.TextField(blank=True)
    result_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['exam', 'student']
        ordering = ['-result_date']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.title} - {self.grade}"


class Notification(models.Model):
    """User Notifications"""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"