# ReviewVerse - Quick Reference Guide

## 📚 Documentation Files Generated

### 1. **PEER_REVIEW_SYSTEM.md** - Complete System Overview
- Project overview and key features
- System architecture and models
- User workflows (teacher/student)
- Security features
- Setup instructions

### 2. **CODE_EXPLANATIONS.md** - Detailed Code Guide
- Models with annotations
- Forms with validation logic
- Views with business logic
- Templates structure
- Workflow scenarios with SQL examples

---

## 🎯 Core Components Summary

### Models (Database Tables)

| Model | Purpose | Key Fields |
|-------|---------|------------|
| **User** | Custom user model | username, email, is_teacher, is_student |
| **Assignment** | Teacher-created assignments | title, description, deadline, created_by |
| **Submission** | Student submissions | assignment, student, content, file, teacher_grade |
| **PeerReview** | Peer reviews of submissions | submission, reviewer, feedback, grade |

### Key Relationships

```
Teacher (User)
    ↓ creates
Assignment
    ↓ receives
Submission (from Student)
    ↓ reviewed by
PeerReview (by other Students)
    ↓ graded by
Teacher (Official grade)
```

---

## 🔐 Validation Rules

### Grade Validation
```
Peer Review Grade: 1-100 (required)
Teacher Grade: 1-100 (required)
```

### Feedback Validation
```
Peer Review Feedback: Minimum 10 characters
File Upload: PDF, DOC, DOCX only
```

### Unique Constraints
```
One submission per (assignment, student)
One peer review per (submission, reviewer)
```

---

## 🚀 Database Operations

### Create Teacher User
```python
from core.models import User

teacher = User.objects.create_user(
    username='teacher1',
    email='teacher@example.com',
    password='Teacher@123',
    is_teacher=True,
    is_student=False
)
```

### Create Assignment
```python
from core.models import Assignment
from django.utils import timezone

assignment = Assignment.objects.create(
    title='Project 1',
    description='Build a web app',
    deadline=timezone.now() + timezone.timedelta(days=7),
    created_by=teacher
)
```

### Submit Assignment
```python
from core.models import Submission

submission = Submission.objects.create(
    assignment=assignment,
    student=student,
    content='Code and documentation...'
)
```

### Create Peer Review
```python
from core.models import PeerReview

review = PeerReview.objects.create(
    submission=submission,
    reviewer=peer_student,
    feedback='Great implementation! Consider optimizing...',
    grade=85
)
```

### Query Examples
```python
# Get all submissions for assignment
assignment.submissions.all()

# Get all reviews of a submission
submission.peer_reviews.all()

# Get teacher's assignments
teacher.assignments_created.all()

# Get student's submissions
student.submissions.all()

# Get reviews given by student
student.reviews_given.all()

# Get unreviewed submissions
reviewed = PeerReview.objects.filter(reviewer=user).values_list('submission_id')
unreviewed = Submission.objects.exclude(student=user).exclude(id__in=reviewed)
```

---

## 📋 URL Routes

### Authentication
```
GET  /              → Home page (redirects to dashboard if logged in)
GET  /login/        → Login page
GET  /logout/       → Logout
GET  /register/     → Registration page
POST /register/     → Create new account
```

### Dashboard
```
GET  /dashboard/    → Route to appropriate dashboard
```

### Teacher Views
```
GET  /assignment/create/              → Create assignment form
POST /assignment/create/              → Submit new assignment
GET  /assignment/<id>/submissions/    → View all submissions
GET  /submission/<id>/reviews/        → View peer reviews of submission
GET  /submission/<id>/grade/          → Grade submission form
POST /submission/<id>/grade/          → Submit grade
```

### Student Views
```
GET  /assignment/<id>/submit/         → Submit assignment form
POST /assignment/<id>/submit/         → Submit assignment
GET  /submission/<id>/review/         → Review submission form
POST /submission/<id>/review/         → Submit peer review
```

---

## 🎨 Form Fields

### UserRegistrationForm
- username (required)
- email (required)
- password1 (required, validated)
- password2 (required, must match password1)
- role (required, choice: Student/Teacher)

### PeerReviewForm
- feedback (required, min 10 characters)
- grade (required, min 1, max 100)

### GradeSubmissionForm
- teacher_grade (required, min 1, max 100)
- teacher_remarks (optional)

---

## ✅ Validation Error Messages

| Error | Cause |
|-------|-------|
| "Grade must be an integer between 1 and 100." | Grade outside 1-100 range |
| "Feedback must be at least 10 characters long." | Peer feedback too short |
| "You cannot review your own submission." | Attempting self-review |
| "You have already reviewed this submission." | Duplicate review attempt |
| "The deadline for this assignment has passed." | Late submission |
| "You have already submitted this assignment." | Duplicate submission |
| "Submission must include either text content or a file." | Empty submission |

---

## 🔍 Debugging Tips

### Check User Roles
```python
user = User.objects.get(username='john')
print(f"Is teacher: {user.is_teacher}")
print(f"Is student: {user.is_student}")
```

### Verify Submission
```python
submission = Submission.objects.get(id=1)
print(f"Status: {submission.submitted_at}")
print(f"Teacher grade: {submission.teacher_grade}")
print(f"Reviews: {submission.peer_reviews.count()}")
```

### Check Peer Reviews
```python
reviews = PeerReview.objects.filter(submission=submission)
for review in reviews:
    print(f"{review.reviewer.username}: {review.grade}/100")
    print(f"Feedback: {review.feedback}")
```

### View Database Migrations
```bash
python manage.py showmigrations
python manage.py sqlmigrate core 0004
```

---

## 🆘 Common Issues & Solutions

### Issue: "ImportError: cannot import name 'PasswordInput'"
**Solution:** Use `forms.PasswordInput` not `PasswordInput` directly
```python
# Wrong
from django.contrib.auth.forms import PasswordInput

# Correct
from django import forms
self.fields['password1'].widget = forms.PasswordInput(attrs={...})
```

### Issue: "User matching query does not exist"
**Solution:** Check user exists before accessing
```python
# Use get_object_or_404 instead of .get()
user = get_object_or_404(User, username='teacher1')

# Or check existence
if User.objects.filter(username='teacher1').exists():
    user = User.objects.get(username='teacher1')
```

### Issue: "You are attempting to set a non-existent field 'is_teacher'"
**Solution:** Migrate after updating User model
```bash
python manage.py makemigrations
python manage.py migrate
```

### Issue: "Unique constraint failed"
**Solution:** Check for duplicate records
```python
# For submission - only one per assignment
if Submission.objects.filter(assignment=assign, student=user).exists():
    return "Already submitted"

# For peer review - only one per submission
if PeerReview.objects.filter(submission=sub, reviewer=user).exists():
    return "Already reviewed"
```

---

## 📱 Test Accounts

| Role | Username | Password | Email |
|------|----------|----------|-------|
| Teacher | teacher1 | Teacher@123 | teacher@example.com |
| Student | student1 | Student@123 | student@example.com |

---

## 🧪 Testing Peer Review Flow

### Step 1: Login as Teacher
```
URL: http://localhost:8000/login/
Username: teacher1
Password: Teacher@123
```

### Step 2: Create Assignment
```
Click "Create Assignment"
Title: "Project Assignment"
Description: "Build a web application"
Deadline: (future date)
Click "Submit"
```

### Step 3: Login as Student
```
Logout and login with:
Username: student1
Password: Student@123
```

### Step 4: Submit Assignment
```
Dashboard shows pending assignment
Click "Submit"
Enter content or upload file
Click "Submit Assignment"
```

### Step 5: Create Another Student Account
```
Register new account with:
Username: student2
Password: Student@123
Role: Student
```

### Step 6: Login as Student 2, Submit Assignment
```
Same as Step 4
```

### Step 7: Login as Student 1, Review Student 2's Work
```
Dashboard shows "Submissions to Review"
Click "Review"
Enter feedback (10+ characters)
Enter grade (1-100)
Click "Submit Review"
```

### Step 8: Login as Teacher, Grade Submission
```
Dashboard → Select Assignment → View Submissions
Click "Grade" on a submission
View all peer reviews
Enter official grade (1-100) and remarks
Click "Submit Official Grade"
```

### Step 9: Verify from Student Dashboard
```
Student sees:
- Their submissions with teacher's grade
- Peer reviews they received
- Reviews they've submitted
```

---

## 📊 Database Schema

### core_user
```sql
id INTEGER PRIMARY KEY
username VARCHAR(150) UNIQUE
email VARCHAR(254)
is_teacher BOOLEAN
is_student BOOLEAN
-- inherited from AbstractUser: password, is_staff, is_superuser, etc.
```

### core_assignment
```sql
id INTEGER PRIMARY KEY
title VARCHAR(200)
description TEXT
deadline DATETIME
created_by_id INTEGER (FK to core_user)
created_at DATETIME
```

### core_submission
```sql
id INTEGER PRIMARY KEY
assignment_id INTEGER (FK to core_assignment)
student_id INTEGER (FK to core_user)
content TEXT NULL
file VARCHAR(100) NULL (path to file)
teacher_grade INTEGER NULL (validated 1-100)
teacher_remarks TEXT NULL
submitted_at DATETIME
UNIQUE(assignment_id, student_id)
```

### core_peerreview
```sql
id INTEGER PRIMARY KEY
submission_id INTEGER (FK to core_submission)
reviewer_id INTEGER (FK to core_user)
feedback TEXT
grade INTEGER (validated 1-100)
created_at DATETIME
UNIQUE(submission_id, reviewer_id)
```

---

## 🔗 Related Files

- **Models:** `core/models.py`
- **Forms:** `core/forms.py`
- **Views:** `core/views.py`
- **URLs:** `core/urls.py`
- **Templates:** `core/templates/core/` and `core/templates/registration/`
- **Settings:** `peer_review_hub/settings.py`
- **Full System Docs:** `PEER_REVIEW_SYSTEM.md`
- **Code Details:** `CODE_EXPLANATIONS.md`

---

## 🎓 Learning Path

1. **Start Here:** Read this Quick Reference
2. **System Overview:** Read `PEER_REVIEW_SYSTEM.md`
3. **Code Details:** Study `CODE_EXPLANATIONS.md`
4. **Build:** Review the actual code files
5. **Test:** Follow the testing flow above
6. **Extend:** Add new features building on existing structure

---

## 💡 Key Takeaways

✅ **Role-Based Access:** Teachers create → Students submit → Peers review
✅ **Validation at Multiple Levels:** Form validation + Model validators + View checks
✅ **Data Integrity:** Django's unique_together ensures no duplicates
✅ **Security:** @login_required + permission checks on all views
✅ **User-Friendly:** Forms handle HTML rendering + error messages
✅ **Scalable:** Uses Django ORM for efficient database queries

---

Generated: 2026-02-22
Version: 1.0
