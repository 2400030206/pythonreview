from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)

    def __str__(self):
        role = "Teacher" if self.is_teacher else "Student" if self.is_student else "Admin"
        return f"{self.username} ({role})"

class Assignment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments_created', limit_choices_to={'is_teacher': True})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

from django.core.validators import FileExtensionValidator

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions', limit_choices_to={'is_student': True})
    content = models.TextField(blank=True, null=True, help_text="Submit your work here. You can include links to external files if needed.")
    file = models.FileField(
        upload_to='submissions/', 
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        blank=True, 
        null=True,
        help_text="Upload a PDF or Word document."
    )
    teacher_grade = models.IntegerField(
        null=True, 
        blank=True, 
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Official grade from teacher (1-100)"
    )
    teacher_remarks = models.TextField(blank=True, null=True, help_text="Remarks from teacher")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('assignment', 'student') # A student can only submit once per assignment

    def __str__(self):
        return f"{self.student.username}'s submission for {self.assignment.title}"

class PeerReview(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='peer_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given', limit_choices_to={'is_student': True})
    feedback = models.TextField(help_text="Provide constructive feedback for your peer.")
    grade = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Grade from 1 to 100"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('submission', 'reviewer') # A student can only review a specific submission once

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.submission}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('submission', 'New Submission'),
        ('review', 'New Review Received'),
        ('grade', 'Grade Posted'),
        ('assignment', 'New Assignment'),
        ('system', 'System Message'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    related_submission = models.ForeignKey(Submission, on_delete=models.CASCADE, null=True, blank=True)
    related_assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.username} - {self.title}"


# ============ NEW FEATURES: ADVANCED ACADEMIC FEATURES ============

class GradeTrend(models.Model):
    """Track grade history for trend analysis"""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grade_trends')
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='grade_trends')
    grade = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['student', '-recorded_at']
    
    def __str__(self):
        return f"Grade trend for {self.student.username}: {self.grade}"


class AssignmentRubric(models.Model):
    """Define grading criteria for assignments"""
    assignment = models.OneToOneField(Assignment, on_delete=models.CASCADE, related_name='rubric')
    title = models.CharField(max_length=200)
    description = models.TextField()
    total_points = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Rubric for {self.assignment.title}"


class RubricCriteria(models.Model):
    """Individual criteria in a rubric"""
    rubric = models.ForeignKey(AssignmentRubric, on_delete=models.CASCADE, related_name='criteria')
    name = models.CharField(max_length=200)
    description = models.TextField()
    points = models.IntegerField()
    
    class Meta:
        verbose_name_plural = "Rubric Criteria"
    
    def __str__(self):
        return f"{self.name} ({self.points} pts)"


class ReviewQualityMetric(models.Model):
    """Track the quality of peer reviews"""
    review = models.OneToOneField(PeerReview, on_delete=models.CASCADE, related_name='quality_metric')
    feedback_length = models.IntegerField()  # Character count
    constructiveness_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 scale for constructiveness"
    )
    specificity_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1-5 scale for specificity"
    )
    overall_quality = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Overall quality percentage"
    )
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quality metric for review by {self.review.reviewer.username}"


class DeadlineReminder(models.Model):
    """Track deadline reminders sent to students"""
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='reminders')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deadline_reminders')
    reminder_type = models.CharField(
        max_length=20,
        choices=[('24h', '24 Hours Before'), ('7d', '7 Days Before'), ('1d', '1 Day Before')],
        default='1d'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('assignment', 'student', 'reminder_type')
    
    def __str__(self):
        return f"Reminder for {self.student.username} - {self.assignment.title}"


class RevisionSubmission(models.Model):
    """Track multiple submission attempts (revision tracking)"""
    original_submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='revisions')
    revision_number = models.IntegerField(default=1)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to='submissions/revisions/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(100)])
    improvement = models.IntegerField(null=True, blank=True, help_text="Grade improvement from previous")
    
    class Meta:
        ordering = ['original_submission', 'revision_number']
    
    def __str__(self):
        return f"Revision {self.revision_number} of {self.original_submission}"


class FeedbackSummary(models.Model):
    """Summarize peer feedback for a submission"""
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='feedback_summary')
    average_peer_grade = models.FloatField()
    total_reviews = models.IntegerField()
    positive_feedback_count = models.IntegerField(default=0)
    improvement_feedback_count = models.IntegerField(default=0)
    common_themes = models.TextField(blank=True, help_text="Common themes in feedback")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback summary for {self.submission}"


class PerformanceInsight(models.Model):
    """Generate performance insights and recommendations"""
    INSIGHT_TYPES = [
        ('improvement', 'Shows Improvement'),
        ('declining', 'Declining Performance'),
        ('excellent', 'Excellent Performance'),
        ('struggling', 'Struggling'),
        ('consistent', 'Consistent Performance'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_insights')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    message = models.TextField()
    recommendation = models.TextField()
    trend_percentage = models.FloatField(help_text="Percentage change in performance")
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Insight for {self.student.username} - {self.get_insight_type_display()}"


class ClassAnalytics(models.Model):
    """Teacher-level class analytics"""
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_analytics_records')
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='class_analytics')
    average_grade = models.FloatField()
    highest_grade = models.IntegerField()
    lowest_grade = models.IntegerField()
    submission_rate = models.FloatField(help_text="Percentage of students who submitted")
    on_time_submission_count = models.IntegerField()
    late_submission_count = models.IntegerField()
    top_performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='top_performer_in')
    at_risk_students = models.ManyToManyField(User, related_name='at_risk_in_assignments', blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analytics for {self.assignment.title} by {self.teacher.username}"
