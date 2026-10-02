# Changes made to the real MEDSRAVTS backend

## Bugs fixed (pre-existing, found while wiring in the new features)
1. `core/routing.py` — the websocket URL pattern had an unterminated string
   literal (`r'ws/notifications/,` — missing the closing quote before the
   comma), which is a SyntaxError. Fixed to `r'ws/notifications/$'`.
2. `meds/asgi.py` — was routing to a throwaway inline `NotificationConsumer`
   that just echoes messages, completely bypassing `core/consumers.py`'s
   real `NotificationConsumer` (per-user groups, unread counts, DB-backed
   notifications). Now imports `core.routing.websocket_urlpatterns` so the
   real consumer is actually used.
3. `core/management/__init__.py` and `core/management/commands/__init__.py`
   were missing (only a mistyped `_innit_.py` existed, which Django's
   app-loader doesn't recognize as a package marker), so
   `populate_samples` was never discoverable by `manage.py`. Added the
   correct `__init__.py` files.
4. `EnrollmentSerializer` / `PaymentSerializer` — `fields = '__all__'` plus
   `perform_create()` setting `student`/`user` from `request.user` meant
   enrollment/payment creation was throwing `"This field is required"` (DRF's
   auto-generated `UniqueTogetherValidator` on `Enrollment` also forces a
   field to be present even with `required: False` in `extra_kwargs` — a
   known DRF gotcha). Fixed with
   `student = serializers.HiddenField(default=serializers.CurrentUserDefault())`
   on `EnrollmentSerializer`, and `extra_kwargs` on `PaymentSerializer`.
5. Notifications for enrollment/payment were being written to the DB via
   `Notification.objects.create(...)` but never pushed over the socket
   (nothing called `consumers.send_notification_to_user`, and asgi.py wasn't
   even wired to the real consumer — see #2). Both now go through a new
   `notify_user()` helper in `views.py` that does both.

## New features (matching the React frontend's Gallery pages, CEO Export
Center, Specialist course-scheduling/marking/feedback/attendance, and
Student grades/certificates)

- **Models** (`core/models.py`): `GalleryPhoto`, `Schedule`, `Grade`,
  `Feedback`, `Attendance`, `Allocation`.
- **Serializers**: matching serializers for all of the above, plus
  `UserDirectorySerializer` for the CEO's export/user-directory view.
- **Views** (`core/views.py`):
  - `GalleryPhotoViewSet` — public read, CEO-only upload/delete
    (`/api/gallery/?type=mou|clinical-research`, multipart `type`, `image`,
    `caption`).
  - `ScheduleViewSet`, `GradeViewSet`, `FeedbackViewSet`,
    `AttendanceViewSet` — role-scoped reads (student sees own, instructor
    sees their courses, CEO sees all), instructor/CEO-only writes.
  - `AllocationViewSet` — CEO-only writes, instructor/CEO reads.
  - `user_directory` — CEO-only `/api/users/?role=`.
  - `CertificateViewSet.perform_create` added (was missing) so issuing a
    certificate now also notifies the student.
- **URLs**: all registered in `core/urls.py` via the existing
  `DefaultRouter` pattern, plus `path('users/', ...)`.
- **Admin**: all new models registered in `core/admin.py`, following the
  existing `list_display`/`list_filter` conventions.
- **`core/endpoints.txt`** updated with the new endpoints.

## Verified end-to-end (Django test client, real request/response cycle)
Register (CEO/instructor/student) → create course → allocate instructor →
student self-enrolls → student self-pays → instructor issues certificate →
instructor schedules a class → instructor records a grade → instructor
gives feedback → instructor marks attendance → CEO uploads a real gallery
image → anonymous visitor can view the gallery but not upload/delete →
student cannot create a course (403) → dashboard stats correct for all
three roles → real-time notifications land in the student's `/api/notifications/`
list for every action above.

## Migration
New migration: `core/migrations/0002_feedback_allocation_attendance_galleryphoto_grade_and_more.py`
Run `python manage.py migrate` after deploying.
