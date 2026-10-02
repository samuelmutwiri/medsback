from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Course, Enrollment, Payment, Certificate, Exam, ExamResult, Notification,
    GalleryPhoto, Schedule, Grade, Feedback, Attendance, Allocation,
)
from core.utils.email_utils import send_login_credentials, send_email_changed_notification


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'specialization', 'profile_picture', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """User Registration Serializer — sends HTML welcome email with credentials."""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm', 'first_name',
            'last_name', 'role', 'phone', 'specialization'
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """Create user and send HTML credentials email."""
        password = validated_data.pop('password')
        validated_data.pop('password_confirm', None)
        user = User.objects.create_user(password=password, **validated_data)
        # Attach the raw password temporarily for email context
        user._raw_password = password

        # Send credentials email
        if user.email:
            send_login_credentials(user.email, user.username, password)

        return user


class LoginSerializer(serializers.Serializer):
    """User Login Serializer"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid credentials.")


class CourseSerializer(serializers.ModelSerializer):
    """Course Serializer"""
    enrollments_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_enrollments_count(self, obj):
        return obj.enrollments.filter(status='active').count()


class EnrollmentSerializer(serializers.ModelSerializer):
    """Enrollment Serializer"""
    student = serializers.HiddenField(default=serializers.CurrentUserDefault())
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_details = CourseSerializer(source='course', read_only=True)

    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['id', 'enroll_date']


class PaymentSerializer(serializers.ModelSerializer):
    """Payment Serializer"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'payment_date', 'transaction_id']
        extra_kwargs = {'user': {'required': False}}

    def create(self, validated_data):
        import uuid
        validated_data['transaction_id'] = f"TXN{uuid.uuid4().hex[:12].upper()}"
        return super().create(validated_data)


class CertificateSerializer(serializers.ModelSerializer):
    """Certificate Serializer"""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Certificate
        fields = '__all__'
        read_only_fields = ['id', 'issue_date', 'certificate_id']

    def create(self, validated_data):
        import datetime
        year = datetime.datetime.now().year
        count = Certificate.objects.filter(issue_date__year=year).count() + 1
        validated_data['certificate_id'] = f"MEDSRAVTS-{year}-CERT-{count:04d}"
        return super().create(validated_data)


class ExamSerializer(serializers.ModelSerializer):
    """Exam Serializer"""
    course_name = serializers.CharField(source='course.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Exam
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'created_by']


class ExamResultSerializer(serializers.ModelSerializer):
    """Exam Result Serializer"""
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)

    class Meta:
        model = ExamResult
        fields = '__all__'
        read_only_fields = ['id', 'result_date']

    def create(self, validated_data):
        marks = validated_data['marks_obtained']
        total = validated_data['exam'].total_marks
        percentage = (marks / total) * 100
        validated_data['percentage'] = percentage

        if percentage >= 90:
            grade = 'A+'
        elif percentage >= 80:
            grade = 'A'
        elif percentage >= 70:
            grade = 'B+'
        elif percentage >= 60:
            grade = 'B'
        elif percentage >= 50:
            grade = 'C'
        else:
            grade = 'F'

        validated_data['grade'] = grade
        validated_data['passed'] = percentage >= (validated_data['exam'].passing_marks / total) * 100
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """Notification Serializer"""
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile with nullable fields.
    Sends HTML notification email when email address changes.
    """
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'specialization',
            'profile_picture'
        ]
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'email': {'required': False},
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},
            'specialization': {'required': False, 'allow_blank': True, 'allow_null': True},
            'profile_picture': {'required': False, 'allow_null': True},
        }

    def validate_email(self, value):
        """Ensure email is unique if being updated."""
        if value:
            user = self.context['request'].user
            if User.objects.exclude(pk=user.pk).filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use.")
        return value

    def update(self, instance, validated_data):
        """Update profile and trigger email change notification if email changed."""
        old_email = instance.email
        new_email = validated_data.get('email', old_email)

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if new_email and old_email and old_email != new_email:
            send_email_changed_notification(instance.username, old_email, new_email)

        return instance


class GalleryPhotoSerializer(serializers.ModelSerializer):
    """Gallery Photo Serializer — backs the MoU Gallery and Clinical Research Gallery pages."""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryPhoto
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_by', 'created_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class ScheduleSerializer(serializers.ModelSerializer):
    """Schedule Serializer — specialist course scheduling and calendars."""
    course_name = serializers.CharField(source='course.name', read_only=True)
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)

    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {'instructor': {'required': False}}


class GradeSerializer(serializers.ModelSerializer):
    """Grade Serializer — specialist marking / gradebook."""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Grade
        fields = '__all__'
        read_only_fields = ['id', 'marked_by', 'created_at']


class FeedbackSerializer(serializers.ModelSerializer):
    """Feedback Serializer — specialist feedback to students."""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ['id', 'given_by', 'created_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """Attendance Serializer."""
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'marked_by']


class AllocationSerializer(serializers.ModelSerializer):
    """Allocation Serializer — CEO assigns specialists to courses."""
    instructor_name = serializers.CharField(source='instructor.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)

    class Meta:
        model = Allocation
        fields = '__all__'
        read_only_fields = ['id', 'allocated_by', 'allocated_at']


class UserDirectorySerializer(serializers.ModelSerializer):
    """Lightweight user listing for the CEO's Export Center (enrolled students,
    specialist directory, etc.)."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'created_at']
