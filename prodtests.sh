#!/bin/bash

# -----------------------------
# Production API Test Script
# -----------------------------
# Session + CSRF authenticated requests for production
# -----------------------------

# Base URL of production
BASE_URL="http://18.142.187.35"
COOKIE_FILE="cookies.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper function for section headers
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Fetch CSRF token
get_csrf_token() {
    CSRF_TOKEN=$(grep csrftoken $COOKIE_FILE | awk '{print $7}')
    echo "$CSRF_TOKEN"
}

# -----------------------------
# 0. Initialize cookies and get CSRF token
# -----------------------------
print_section "0. FETCH CSRF TOKEN"
curl -s -c "$COOKIE_FILE" "$BASE_URL/api/auth/login/" > /dev/null
CSRF_TOKEN=$(get_csrf_token)
echo -e "${YELLOW}CSRF Token: $CSRF_TOKEN${NC}"

# -----------------------------
# 1. Register User (optional if new)
# -----------------------------
print_section "1. REGISTERING NEW USER"
curl -s -X POST "$BASE_URL/api/auth/register/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" -c "$COOKIE_FILE" \
    -d '{
        "username": "student1",
        "email": "student1@test.com",
        "password": "test123",
        "password_confirm": "test123",
        "role": "student",
        "first_name": "John",
        "last_name": "Doe"
    }'

# -----------------------------
# 2. Login and save cookies
# -----------------------------
print_section "2. LOGGING IN"
curl -s -X POST "$BASE_URL/api/auth/login/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" -c "$COOKIE_FILE" \
    -d '{
        "username": "student1",
        "password": "test123"
    }'

# Refresh CSRF token after login
CSRF_TOKEN=$(get_csrf_token)
echo -e "${YELLOW}CSRF Token after login: $CSRF_TOKEN${NC}"

# -----------------------------
# 3. Get Current User Profile
# -----------------------------
print_section "3. GET CURRENT USER PROFILE"
curl -s -X GET "$BASE_URL/api/auth/user/" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -b "$COOKIE_FILE"

# -----------------------------
# 4. List All Courses
# -----------------------------
print_section "4. LIST ALL COURSES"
curl -s -X GET "$BASE_URL/api/courses/" -b "$COOKIE_FILE"

# -----------------------------
# 5. Search Courses
# -----------------------------
print_section "5. SEARCH COURSES (Clinical)"
curl -s -X GET "$BASE_URL/api/courses/search/?q=Clinical&type=" -b "$COOKIE_FILE"

# -----------------------------
# 6. Enroll in Course 1
# -----------------------------
print_section "6. ENROLL IN COURSE 1"
curl -s -X POST "$BASE_URL/api/enrollments/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" \
    -d '{"course":1,"notes":"Excited to start learning"}'

# -----------------------------
# 7. Get My Enrollments
# -----------------------------
print_section "7. GET MY ENROLLMENTS"
curl -s -X GET "$BASE_URL/api/enrollments/" -b "$COOKIE_FILE"

# -----------------------------
# 8. Update Profile - First Name
# -----------------------------
print_section "8. UPDATE PROFILE - FIRST NAME ONLY"
curl -s -X PATCH "$BASE_URL/api/profile/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" \
    -d '{"first_name":"Jane"}'

# -----------------------------
# 9. Update Profile - Email & Phone
# -----------------------------
print_section "9. UPDATE PROFILE - EMAIL AND PHONE"
curl -s -X PATCH "$BASE_URL/api/profile/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" \
    -d '{"email":"jane.doe@test.com","phone":"+91 9999999999"}'

# -----------------------------
# 10. Update Profile - Multiple Fields
# -----------------------------
print_section "10. UPDATE PROFILE - MULTIPLE FIELDS"
curl -s -X PATCH "$BASE_URL/api/profile/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" \
    -d '{"first_name":"Jane","last_name":"Smith","phone":"+91 8888888888"}'

# -----------------------------
# 11. Get Updated Profile
# -----------------------------
print_section "11. GET UPDATED PROFILE"
curl -s -X GET "$BASE_URL/api/profile/" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -b "$COOKIE_FILE"

# -----------------------------
# 12. Create Payment
# -----------------------------
print_section "12. CREATE PAYMENT"
curl -s -X POST "$BASE_URL/api/payments/" \
    -H "Content-Type: application/json" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE" \
    -d '{"course":1,"amount":50000,"method":"upi"}'

# -----------------------------
# 13. Get My Payments
# -----------------------------
print_section "13. GET MY PAYMENTS"
curl -s -X GET "$BASE_URL/api/payments/" -b "$COOKIE_FILE"

# -----------------------------
# 14. Get My Certificates
# -----------------------------
print_section "14. GET MY CERTIFICATES"
curl -s -X GET "$BASE_URL/api/certificates/" -b "$COOKIE_FILE"

# -----------------------------
# 15. Get Exams
# -----------------------------
print_section "15. GET EXAMS"
curl -s -X GET "$BASE_URL/api/exams/" -b "$COOKIE_FILE"

# -----------------------------
# 16. Get Dashboard Stats
# -----------------------------
print_section "16. GET DASHBOARD STATS"
curl -s -X GET "$BASE_URL/api/dashboard/stats/" -b "$COOKIE_FILE"

# -----------------------------
# 17. Get Notifications
# -----------------------------
print_section "17. GET NOTIFICATIONS"
curl -s -X GET "$BASE_URL/api/notifications/" -b "$COOKIE_FILE"

# -----------------------------
# 18. Logout
# -----------------------------
print_section "18. LOGOUT"
curl -s -X POST "$BASE_URL/api/auth/logout/" \
    -H "X-CSRFToken: $CSRF_TOKEN" \
    -H "Referer: $BASE_URL" \
    -b "$COOKIE_FILE"

# -----------------------------
# Done
# -----------------------------
echo -e "\n${GREEN}Production API tests completed!${NC}"
echo -e "${YELLOW}Cookie file saved as: $COOKIE_FILE${NC}"
