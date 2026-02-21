# Register User
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student1",
    "email": "student1@test.com",
    "password": "test123",
    "password_confirm": "test123",
    "role": "student",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "username": "student1",
    "password": "test123"
  }'

# Get Current User
curl -X GET http://localhost:8000/api/auth/user/ \
  -b cookies.txt

# List Courses
curl -X GET http://localhost:8000/api/courses/

# Create Enrollment
curl -X POST http://localhost:8000/api/enrollments/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "course": 1,
    "notes": "Excited to start learning"
  }'