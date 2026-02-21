#!/bin/bash

BASE_URL="http://127.0.0.1:8000"
COOKIE_FILE="cookies.txt"

# 1. Register (Will show error if user exists, which is fine for repeat tests)
echo "--- Registering ---"
curl -X POST $BASE_URL/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "email": "student1@test.com", "password": "test123", "password_confirm": "test123", "role": "student"}'

# 2. Login and save cookies
echo -e "\n\n--- Logging In ---"
curl -X POST $BASE_URL/api/auth/login/ \
  -H "Content-Type: application/json" \
  -c $COOKIE_FILE \
  -d '{"username": "student1", "password": "test123"}'

# 3. Extract CSRF Token from the cookie file
CSRF_TOKEN=$(grep "csrftoken" $COOKIE_FILE | awk '{print $7}')
echo -e "\n\nExtracted CSRF: $CSRF_TOKEN"

# 4. Get User Profile (GET doesn't need CSRF)
echo -e "\n--- User Profile ---"
curl -X GET $BASE_URL/api/auth/user/ -b $COOKIE_FILE

# 5. List Courses
echo -e "\n--- Courses ---"
curl -X GET $BASE_URL/api/courses/

# 6. Create Enrollment (NEEDS CSRF TOKEN)
echo -e "\n--- Enrolling in Course 1 ---"
curl -X POST $BASE_URL/api/enrollments/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF_TOKEN" \
  -H "Referer: $BASE_URL" \
  -b $COOKIE_FILE \
  -d '{"course": 1, "notes": "Excited to start learning"}'
