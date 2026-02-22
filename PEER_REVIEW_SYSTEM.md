# ReviewVerse - Peer Review System Documentation

## 🎓 Project Overview

**ReviewVerse** is a Django-based assignment submission and peer review system designed for educational institutions. It enables teachers to create assignments, students to submit their work, and peers to review each other's submissions with grades and constructive feedback.

---

## 📋 Key Features

### 1. **User Roles**
- **Teachers:** Create assignments, grade submissions, view peer reviews
- **Students:** Submit assignments, review peer submissions, view grades

### 2. **Assignment Management**
- Teachers create assignments with titles, descriptions, and deadlines
- Automatic deadline validation prevents late submissions
- Students can only submit once per assignment

### 3. **Submission System**
- Students submit assignments with text content and/or file uploads (PDF, DOC, DOCX)
- Teachers can grade submissions (1-100 scale) with remarks
- Submission tracking with timestamps

### 4. **Peer Review System**
- Students review peer submissions (not their own)
- Grade submissions on a scale of 1-100
- Provide constructive feedback (minimum 10 characters)
- Prevent duplicate reviews of the same submission
- Anonymous peer review (only reviewer identified to teacher)

### 5. **Validation & Error Handling**
- Grade validation (must be between 1-100)
- Feedback validation (minimum length requirements)
- File type validation (PDF, DOC, DOCX only)
- Permission checks (teachers/students access control)

---

## 🏗️ System Architecture

### Database Models

```python
User
├── is_teacher (Boolean)
├── is_student (Boolean)
└── inherits from AbstractUser

Assignment
├── title (CharField)
├── description (TextField)
├── deadline (DateTimeField)
├── created_by (ForeignKey to User)
└── created_at (DateTimeField)

Submission
├── assignment (ForeignKey to Assignment)
├── student (ForeignKey to User)
├── content (TextField - optional)
├── file (FileField - optional)
├── teacher_grade (IntegerField, 1-100)
├── teacher_remarks (TextField)
└── submitted_at (DateTimeField)

PeerReview
├── submission (ForeignKey to Submission)
├── reviewer (ForeignKey to User - student)
├── feedback (TextField, min 10 chars)
├── grade (IntegerField, 1-100)
└── created_at (DateTimeField)
```

### Validation Rules

**Grade Fields:**
- `MinValueValidator(1)` - Minimum grade is 1
- `MaxValueValidator(100)` - Maximum grade is 100

**Feedback Field:**
- Minimum length: 10 characters
- Required for peer reviews

**File Uploads:**
- Allowed extensions: PDF, DOC, DOCX
- Upload directory: `submissions/`

---

## 🔀 Workflow

### For Teachers:
1. **Create Assignment**
   - Navigate to "Create Assignment"
   - Fill in title, description, and deadline
   - Submissions are restricted after deadline

2. **View Submissions**
   - See all student submissions for an assignment
   - Check count of peer reviews received
   - Click to grade individual submissions

3. **Grade Submissions**
   - View student's submission content/files
   - Enter official grade (1-100)
   - Add remarks (optional)
   - Save and return to submissions list

4. **View Peer Reviews**
   - Click on submission to see all peer reviews
   - Read feedback and grades from student peers
   - Use this to inform official grading

### For Students:
1. **View Dashboard**
   - See pending assignments (before deadline)
   - View own submissions and teacher grades
   - See peer submissions to review

2. **Submit Assignment**
   - Access assignment details
   - Submit either text content or file upload (or both)
   - Cannot re-submit after first submission
   - Error if deadline has passed

3. **Review Peer Submission**
   - View peer's submission (anonymous peer shown)
   - Read assignment requirements
   - Provide feedback (10+ characters)
   - Enter grade (1-100)
   - Submit review (cannot review own work or same submission twice)

4. **View Grades**
   - Check teacher's official grade
   - Read teacher's remarks
   - View all peer reviews of their submission

---

## 📁 Code Structure

### Models (`models.py`)
```python
class User(AbstractUser):
    """Custom user model with teacher/student roles"""
    - is_teacher: Boolean flag for teacher role
    - is_student: Boolean flag for student role
    
class Assignment(models.Model):
    """Assignment created by teachers"""
    - title: Assignment name
    - description: Assignment details
    - deadline: Submission deadline
    - created_by: Teacher who created it
    - created_at: Creation timestamp

class Submission(models.Model):
    """Student submission for an assignment"""
    - assignment: Parent assignment
    - student: Student who submitted
    - content: Text submission
    - file: File attachment (PDF/DOC/DOCX)
    - teacher_grade: Official grade (1-100)
    - teacher_remarks: Teacher feedback
    - submitted_at: Submission timestamp
    
class PeerReview(models.Model):
    """Peer review of a submission"""
    - submission: Reviewed submission
    - reviewer: Student reviewer
    - feedback: Review comments (min 10 chars)
    - grade: Peer grade (1-100)
    - created_at: Review timestamp
```

### Forms (`forms.py`)
```python
UserRegistrationForm
├── Fields: username, email, password1, password2, role
├── Validators: Built-in password validation
└── Widgets: Styled with Tailwind CSS classes

PeerReviewForm (ModelForm)
├── Fields: feedback, grade
├── Validators: Grade 1-100, Feedback min 10 chars
└── Widgets: Textarea, NumberInput with styling

GradeSubmissionForm
├── Fields: teacher_grade, teacher_remarks
├── Validators: Grade 1-100, remarks optional
└── Widgets: NumberInput, Textarea with styling
```

### Views (`views.py`)

**Authentication:**
- `home()` - Redirect authenticated users to dashboard
- `register()` - User registration with role selection
- `dashboard()` - Route to teacher/student dashboard

**Teacher Views:**
- `teacher_dashboard()` - Display teacher's assignments
- `create_assignment()` - Create new assignment
- `view_submissions()` - List submissions for assignment
- `view_peer_reviews()` - Show all peer reviews of submission
- `grade_submission()` - Grade and add remarks to submission

**Student Views:**
- `student_dashboard()` - Display pending assignments, submissions, peers to review
- `submit_assignment()` - Submit assignment (text/file)
- `review_submission()` - Review peer submission with grade & feedback

**Permission Checks:**
- Only logged-in users can access protected views
- Teachers can only manage their own assignments
- Students can only review others' work
- Prevents self-review and duplicate reviews

### Templates (`templates/core/`)

**`review_submission.html`**
- Displays peer's submission (anonymous)
- Form to submit feedback and grade
- Validation error messages
- Styled with Tailwind CSS

**`grade_submission.html`**
- Shows student submission details
- Form for teacher to enter grade (1-100)
- Optional remarks field
- Button updates or saves new grade

**`registration/register.html`**
- User registration form
- Username, email, password fields
- Role selection (Student/Teacher) as radio buttons
- Styled input fields with validation

---

## 🔐 Security Features

1. **CSRF Protection**
   - `{% csrf_token %}` in all forms
   - Prevents cross-site request forgery

2. **Permission Checks**
   ```python
   @login_required  # Only logged-in users
   if not request.user.is_teacher:  # Role-based access
   if submission.assignment.created_by != request.user:  # Ownership check
   ```

3. **Data Validation**
   ```python
   # Grade validation (1-100)
   validators=[MinValueValidator(1), MaxValueValidator(100)]
   
   # File type validation
   validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
   
   # Feedback minimum length
   if len(feedback.strip()) < 10:
       raise ValidationError('Feedback must be at least 10 characters long.')
   ```

4. **Unique Constraints**
   ```python
   # One submission per student per assignment
   class Meta:
       unique_together = ('assignment', 'student')
   
   # One review per student per submission
   class Meta:
       unique_together = ('submission', 'reviewer')
   ```

---

## 🚀 Running the Application

### Prerequisites
- Python 3.8+
- Django 4.2+
- SQLite3

### Setup
```bash
# Install dependencies
pip install django

# Run migrations
python manage.py migrate

# Create test users
python manage.py shell
>> from core.models import User
>> User.objects.create_user(username='teacher1', password='Teacher@123', is_teacher=True)
>> User.objects.create_user(username='student1', password='Student@123', is_student=True)
>> exit()

# Start server
python manage.py runserver
```

### Test Credentials
- **Teacher:** `teacher1` / `Teacher@123`
- **Student:** `student1` / `Student@123`

---

## 📊 User Flows

### Peer Review Flow

```
Student Dashboard
    ↓
Select "Review Peer Submission"
    ↓
View Peer's Submission
    ↓
Read Assignment Requirements
    ↓
Write Feedback (min 10 chars)
    ↓
Enter Grade (1-100)
    ↓
Submit Review
    ↓
Return to Dashboard
    ↓
[Teacher] View All Peer Reviews
    ↓
Consider Peer Feedback in Official Grading
```

### Grading Flow

```
Teacher Dashboard
    ↓
Select Assignment
    ↓
View All Submissions
    ↓
Select Submission to Grade
    ↓
View Student's Work
    ↓
[Optional] Check Peer Reviews
    ↓
Enter Official Grade (1-100)
    ↓
Add Remarks (optional)
    ↓
Save Grade
    ↓
[Student] View Official Grade on Dashboard
```

---

## 🐛 Error Handling

### Common Validation Errors

1. **Grade Validation**
   - "Grade must be an integer between 1 and 100."
   - Applied at form and model level

2. **Feedback Validation**
   - "Feedback must be at least 10 characters long."
   - Ensures quality peer reviews

3. **File Validation**
   - "The submitted file must have one of the following extensions: 'pdf, doc, docx'."
   - Prevents unsupported file types

4. **Deadline Errors**
   - "The deadline for this assignment has passed."
   - Prevents late submissions

5. **Permission Errors**
   - "You cannot review your own submission."
   - "You have already reviewed this submission."
   - "You do not have permission to grade this submission."

---

## 🎨 UI/UX Features

1. **Responsive Design**
   - Tailwind CSS for modern styling
   - Mobile-friendly layout
   - Dark/light mode compatible

2. **Form Feedback**
   - Success messages on submission
   - Error alerts for validation failures
   - Help text explaining requirements

3. **Navigation**
   - Clear breadcrumb links
   - Back buttons throughout
   - Consistent menu structure

4. **Visual Hierarchy**
   - Large grade input fields for visibility
   - Distinct sections for submission/feedback
   - Color-coded buttons (primary/secondary)

---

## 📈 Future Enhancements

- [ ] Rubric-based grading with criteria
- [ ] Average peer grade calculation
- [ ] Review quality metrics
- [ ] Bulk import of students/assignments
- [ ] Email notifications for submissions
- [ ] Anonymous peer profile generation
- [ ] Review moderation by teacher
- [ ] Plagiarism detection integration
- [ ] Export grades to CSV

---

## 📞 Support

For issues or questions about the peer review system, check:
1. Database migrations are up to date: `python manage.py migrate`
2. All form fields are properly validated
3. User roles are correctly set (is_teacher/is_student)
4. File permissions for uploads directory
5. Django check: `python manage.py check`
