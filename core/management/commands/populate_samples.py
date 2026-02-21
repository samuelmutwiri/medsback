from django.core.management.base import BaseCommand
from core.models import User, Course
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate initial data for MEDSRAVTS'

    def handle(self, *args, **kwargs):
        # Create users
        ceo = User.objects.create_user(
            username='ceo',
            email='ceo@medsravts.com',
            password='ceo123',
            role='ceo',
            first_name='Admin',
            last_name='Kumar'
        )
        
        instructor = User.objects.create_user(
            username='instructor',
            email='instructor@medsravts.com',
            password='inst123',
            role='instructor',
            first_name='Prof',
            last_name='Sharma',
            specialization='Clinical Research'
        )
        
        student = User.objects.create_user(
            username='student',
            email='student@medsravts.com',
            password='stu123',
            role='student',
            first_name='Rajesh',
            last_name='Patel'
        )
        
        # Create courses
        courses_data = [
            {
                'name': 'Clinical Research',
                'course_type': 'PG',
                'duration': '1 year',
                'eligibility': 'BPharm, MPharm, PharmD, MBBS, MD',
                'mode': 'hybrid',
                'fees': 50000,
                'description': 'Comprehensive program in clinical research methodology'
            },
            {
                'name': 'Pharmacovigilance',
                'course_type': 'Certificate',
                'duration': '6 months',
                'eligibility': 'BPharm, MPharm, PharmD, MBBS, MD',
                'mode': 'online',
                'fees': 30000,
                'description': 'Learn drug safety and monitoring techniques'
            },
            {
                'name': 'Clinical Data Management',
                'course_type': 'Fellowship',
                'duration': '1 year',
                'eligibility': 'BPharm, MPharm, PharmD, MBBS, MD',
                'mode': 'hybrid',
                'fees': 60000,
                'description': 'Master clinical data management and analysis'
            },
            {
                'name': 'MS in Pharmacology',
                'course_type': 'MS',
                'duration': '2 years',
                'eligibility': 'BPharm, MPharm, PharmD',
                'mode': 'offline',
                'fees': 120000,
                'description': 'Advanced degree in pharmacology'
            },
            {
                'name': 'MS in Clinical Research',
                'course_type': 'MS',
                'duration': '2 years',
                'eligibility': 'BPharm, MPharm, PharmD, MBBS',
                'mode': 'hybrid',
                'fees': 130000,
                'description': 'Master of Science in Clinical Research'
            },
        ]
        
        for course_data in courses_data:
            Course.objects.create(**course_data, created_by=ceo)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated initial data'))