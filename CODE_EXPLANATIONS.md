# ReviewVerse - Detailed Code Explanations

## 1️⃣ MODELS - Database Structure (models.py)

### Overview
Models define the database structure and relationships for the peer review system.

### User Model
```python
class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    - Adds teacher/student role flags for permission control
    """
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    
    def __str__(self):
        role = "Teacher" if self.is_teacher else "Student" if self.is_student else "Admin"
        return f"{self.username} ({role})"
    
    # Usage:
    # user = User.objects.create_user(username='john', password='pass123', is_student=True)
    # if user.is_teacher: grant_teacher_permissions()
```

### Assignment Model
```python
class Assignment(models.Model):
    """
    Represents an assignment created by a teacher
    - Tracks: title, description, deadline, creator, creation time
    - One teacher can create multiple assignments
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()  # Submission cutoff
    
    # Foreign key to User (teacher who created this)
    # related_name='assignments_created' allows reverse access: teacher.assignments_created.all()
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assignments_created',
        limit_choices_to={'is_teacher': True}  # Only teachers
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Usage:
    # assignment = Assignment.objects.filter(created_by=teacher).first()
    # assignment.submissions.all()  # Get all submissions for this assignment
```

### Submission Model
```python
class Submission(models.Model):
    """
    Represents a student's submission for an assignment
    - Stores both text content and file uploads
    - Teacher can grade with official grade and remarks
    - Multiple peer reviews can exist for one submission
    """
    # Foreign keys establish relationships
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE,  # Delete submission if assignment deleted
        related_name='submissions'  # Access via: assignment.submissions.all()
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions',
        limit_choices_to={'is_student': True}  # Only students
    )
    
    # Submission content (student can submit either text OR file OR both)
    content = models.TextField(
        blank=True, 
        null=True,
        help_text="Submit your work here. Include links if needed."
    )
    
    # File upload (validated to accept only PDF, DOC, DOCX)
    file = models.FileField(
        upload_to='submissions/',  # Files saved to: media/submissions/filename
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        blank=True,
        null=True,
        help_text="Upload a PDF or Word document."
    )
    
    # Teacher grading (1-100 scale with validators)
    teacher_grade = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Official grade from teacher (1-100)"
    )
    
    # Teacher remarks/feedback
    teacher_remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Remarks from teacher"
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # UNIQUE CONSTRAINT: Student can only submit ONCE per assignment
    class Meta:
        unique_together = ('assignment', 'student')
    
    # Usage:
    # submission = Submission.objects.get(assignment=assign, student=student1)
    # submission.peer_reviews.all()  # Get all peer reviews of this submission
```

### PeerReview Model
```python
class PeerReview(models.Model):
    """
    Represents a peer review - one student reviewing another's submission
    - Stores feedback (text) and grade (1-100)
    - Anonymous to students but tracked for teachers
    """
    # Foreign keys
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='peer_reviews'  # Access via: submission.peer_reviews.all()
    )
    
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',  # Access via: student.reviews_given.all()
        limit_choices_to={'is_student': True}
    )
    
    # Review content
    feedback = models.TextField(help_text="Provide constructive feedback for your peer.")
    
    # Peer's grade (1-100)
    grade = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Grade from 1 to 100"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    # UNIQUE CONSTRAINT: Student can only review ONCE per submission
    # Prevents duplicate reviews of same submission by same student
    class Meta:
        unique_together = ('submission', 'reviewer')
    
    # Usage:
    # review = PeerReview.objects.create(
    #     submission=submission,
    #     reviewer=student2,
    #     feedback="Great work!",
    #     grade=85
    # )
```

---

## 2️⃣ FORMS - Input Validation (forms.py)

### Overview
Forms handle data validation and rendering with proper styling.

### UserRegistrationForm
```python
class UserRegistrationForm(UserCreationForm):
    """
    Registration form with role selection
    - Extends Django's UserCreationForm (includes password validation)
    - Adds email field
    - Includes role selection (Student/Teacher)
    """
    
    # Role choices for radio button selection
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,  # Display as radio buttons not dropdown
        initial='student',
        help_text="Select your role in the system.",
        label="Role"
    )
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)  # username, password1, password2, email
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border...',
                'placeholder': 'johndoe',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 appearance-none rounded...',
                'placeholder': 'john@example.com',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields dynamically
        self.fields['password1'].widget = forms.PasswordInput(attrs={...})
        self.fields['password2'].widget = forms.PasswordInput(attrs={...})
    
    def save(self, commit=True):
        """
        Override save to set user role based on selection
        """
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        
        if role == 'teacher':
            user.is_teacher = True
            user.is_student = False
        else:
            user.is_student = True
            user.is_teacher = False
        
        if commit:
            user.save()
        return user
```

### PeerReviewForm
```python
class PeerReviewForm(forms.ModelForm):
    """
    Form for students to submit peer reviews
    - Validates feedback (min 10 characters)
    - Validates grade (1-100)
    """
    
    class Meta:
        model = PeerReview
        fields = ['feedback', 'grade']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide constructive feedback...',
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '1',
                'max': '100',
            })
        }
    
    def clean_grade(self):
        """Validate grade is integer between 1-100"""
        grade = self.cleaned_data.get('grade')
        if grade is not None:
            if not isinstance(grade, int) or not (1 <= grade <= 100):
                raise forms.ValidationError('Grade must be an integer between 1 and 100.')
        return grade
    
    def clean_feedback(self):
        """Validate feedback is at least 10 characters"""
        feedback = self.cleaned_data.get('feedback')
        if feedback and len(feedback.strip()) < 10:
            raise forms.ValidationError('Feedback must be at least 10 characters long.')
        return feedback
```

### GradeSubmissionForm
```python
class GradeSubmissionForm(forms.Form):
    """
    Form for teachers to grade submissions
    - teacher_grade (required): 1-100
    - teacher_remarks (optional): feedback text
    """
    
    teacher_grade = forms.IntegerField(
        label='Grade',
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={...})
    )
    
    teacher_remarks = forms.CharField(
        label='Remarks',
        required=False,  # Optional field
        widget=forms.Textarea(attrs={...})
    )
```

---

## 3️⃣ VIEWS - Business Logic (views.py)

### Overview
Views handle HTTP requests, implement business logic, and render responses.

### Auth Views

```python
@login_required
def dashboard(request):
    """
    Route users to appropriate dashboard based on role
    - Teachers → teacher_dashboard
    - Students → student_dashboard
    - Admins → admin_dashboard
    """
    if request.user.is_teacher:
        return teacher_dashboard(request)
    elif request.user.is_student:
        return student_dashboard(request)
    else:
        return render(request, 'core/admin_dashboard.html')
```

### Teacher Views

```python
@login_required
def grade_submission(request, submission_id):
    """
    Teacher grades a student submission
    
    Steps:
    1. Get submission and verify teacher owns the assignment
    2. Display submission details (content, file, peer reviews)
    3. On POST: validate grade (1-100), save to database
    4. Redirect back to submissions list
    
    Security:
    - @login_required: Only logged-in users
    - is_teacher check: Only teachers can grade
    - Owner verification: Teacher must own the assignment
    """
    
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Verify this teacher owns the assignment
    if submission.assignment.created_by != request.user:
        messages.error(request, 'You do not have permission.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST)
        if form.is_valid():
            # Save grade and remarks to submission
            submission.teacher_grade = form.cleaned_data['teacher_grade']
            submission.teacher_remarks = form.cleaned_data.get('teacher_remarks', '')
            submission.save()
            messages.success(request, 'Grade submitted successfully!')
            return redirect('view_submissions', assignment_id=submission.assignment.id)
    else:
        form = GradeSubmissionForm()
    
    return render(request, 'core/grade_submission.html', {
        'submission': submission,
        'form': form
    })
```

### Student Views

```python
@login_required
def review_submission(request, submission_id):
    """
    Student reviews a peer's submission
    
    Steps:
    1. Get submission and verify not own work
    2. Check student hasn't already reviewed this submission
    3. On POST: validate feedback (10+ chars), grade (1-100), save review
    4. Prevent self-review and duplicate reviews
    
    Validation:
    - cannot review own submission
    - cannot review same submission twice
    - feedback minimum 10 characters
    - grade between 1-100
    """
    
    if not request.user.is_student:
        return redirect('dashboard')
    
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Prevent reviewing own assignment
    if submission.student == request.user:
        messages.error(request, 'You cannot review your own submission.')
        return redirect('dashboard')
    
    # Prevent duplicate reviews
    if PeerReview.objects.filter(submission=submission, reviewer=request.user).exists():
        messages.warning(request, 'You have already reviewed this submission.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PeerReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.submission = submission
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Review submitted successfully!')
            return redirect('dashboard')
        else:
            # Display validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PeerReviewForm()
    
    return render(request, 'core/review_submission.html', {
        'submission': submission,
        'form': form
    })
```

```python
@login_required
def submit_assignment(request, assignment_id):
    """
    Student submits an assignment
    
    Validations:
    1. Assignment must not be past deadline
    2. Student must not have already submitted
    3. Submission must have either text content or file (or both)
    4. File must be PDF, DOC, or DOCX
    5. Content must not be empty
    """
    
    if not request.user.is_student:
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check deadline
    if timezone.now() > assignment.deadline:
        messages.error(request, 'The deadline for this assignment has passed.')
        return redirect('dashboard')
    
    # Check if already submitted
    if Submission.objects.filter(assignment=assignment, student=request.user).exists():
        messages.warning(request, 'You have already submitted this assignment.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
        # At least content or file must be provided
        if content or file:
            Submission.objects.create(
                assignment=assignment,
                student=request.user,
                content=content,
                file=file
            )
            messages.success(request, 'Assignment submitted successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Submission must include either text content or a file.')
    
    return render(request, 'core/submit_assignment.html', {'assignment': assignment})
```

---

## 4️⃣ TEMPLATES - User Interface

### review_submission.html
```html
<!-- Display peer's submission -->
<div class="bg-gray-50 border-b p-6">
    {{ submission.assignment.title }}
    {{ submission.content|default:"No text response" }}
    {% if submission.file %}
        <a href="{{ submission.file.url }}">Download File</a>
    {% endif %}
</div>

<!-- Form to submit review -->
<form method="POST">
    {% csrf_token %}
    
    <!-- Feedback textarea -->
    {{ form.feedback.label_tag }}
    {{ form.feedback }}  <!-- Textarea for feedback -->
    
    <!-- Grade input -->
    {{ form.grade.label_tag }}
    {{ form.grade }}  <!-- Number input 1-100 -->
    
    <!-- Errors -->
    {% if form.feedback.errors %}
        <p class="text-red-600">{{ form.feedback.errors }}</p>
    {% endif %}
    
    <button type="submit">Submit Review</button>
</form>
```

---

## 5️⃣ WORKFLOW SCENARIOS

### Scenario 1: Submit Assignment
```
1. Student views dashboard
   - SQL: SELECT * FROM core_submission WHERE student_id = current_user
   - SQL: SELECT * FROM core_assignment WHERE deadline > now()

2. Student clicks "Submit Assignment"
   - POST /assignment/1/submit/
   - Form validates: content and/or file provided
   - FileValidator checks: filename ends with .pdf, .doc, .docx
   - Unique constraint: (assignment, student) doesn't exist

3. Database insert:
   - INSERT INTO core_submission (assignment_id, student_id, content, file, submitted_at)
   
4. Success message and redirect to dashboard
```

### Scenario 2: Peer Review
```
1. Student sees "Submissions to Review" on dashboard
   - SQL: SELECT * FROM core_submission 
           WHERE student_id != current_user 
           AND id NOT IN (SELECT submission_id FROM core_peerreview WHERE reviewer_id = current_user)
   - Shows up to 3 random submissions

2. Student clicks "Review"
   - GET /submission/5/review/
   - Checks: submission.student != current_user (not own work)
   - Checks: PeerReview.objects.filter(submission=5, reviewer=current_user) is empty

3. Student writes feedback and enters grade
   - Validates: feedback length >= 10 characters
   - Validates: grade (1 <= grade <= 100)

4. Form submission
   - POST /submission/5/review/
   - INSERT INTO core_peerreview (submission_id, reviewer_id, feedback, grade, created_at)
   - Unique constraint ensures no duplicate reviews

5. Redirect to dashboard - review complete
```

### Scenario 3: Teacher Grades Submission
```
1. Teacher views submissions for assignment
   - SQL: SELECT * FROM core_submission WHERE assignment_id = 1 AND assignment.created_by = teacher
   - Shows count of peer reviews for each submission

2. Teacher clicks "Grade"
   - Verifies teacher owns the assignment
   - Displays student's submission content and file

3. Teacher enters grade and remarks
   - Validates: grade (1 <= grade <= 100)
   - Remarks are optional

4. Form submission
   - UPDATE core_submission SET teacher_grade = 85, teacher_remarks = "Good work" WHERE id = 5

5. Student sees updated grade on dashboard
```

---

## 🔑 Key Concepts

### Unique Constraints
Prevent duplicate records:
```python
# Only one submission per (assignment, student) pair
class Meta:
    unique_together = ('assignment', 'student')

# Only one review per (submission, reviewer) pair  
class Meta:
    unique_together = ('submission', 'reviewer')
```

### Foreign Keys
Establish relationships:
```python
# Delete submission if assignment deleted
submission.assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)

# Track which teacher created assignment
assignment.created_by = models.ForeignKey(User, on_delete=models.CASCADE)
```

### Validators
Enforce constraints:
```python
# Grade must be 1-100
validators=[MinValueValidator(1), MaxValueValidator(100)]

# File must be PDF, DOC, DOCX
validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
```

### Decorators
Enforce permissions:
```python
@login_required  # Only authenticated users
def dashboard(request):
    pass

# Then check roles:
if not request.user.is_teacher:
    return redirect('dashboard')
```

---

This documentation provides complete understanding of the peer review system architecture and implementation.
