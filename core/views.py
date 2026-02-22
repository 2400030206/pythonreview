from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .models import Assignment, Submission, PeerReview, Notification, GradeTrend, AssignmentRubric, ReviewQualityMetric, DeadlineReminder, RevisionSubmission, FeedbackSummary, PerformanceInsight, ClassAnalytics
from .forms import UserRegistrationForm, PeerReviewForm, GradeSubmissionForm, CustomPasswordResetForm, CustomSetPasswordForm
from django.utils import timezone
from django.db.models import Count, Q, Avg, Max, Min
import json

User = get_user_model()

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created for {user.username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.is_teacher:
        return teacher_dashboard(request)
    elif request.user.is_student:
        return student_dashboard(request)
    else:
        # For superuser/admin
        return render(request, 'core/admin_dashboard.html')

@login_required
def teacher_dashboard(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
        
    assignments = Assignment.objects.filter(created_by=request.user).order_by('-created_at')
    
    context = {
        'assignments': assignments
    }
    return render(request, 'core/teacher_dashboard.html', context)

@login_required
def student_dashboard(request):
    if not request.user.is_student:
        return redirect('dashboard')
        
    now = timezone.now()
    
    # Active assignments the student hasn't submitted yet
    submitted_assignment_ids = Submission.objects.filter(student=request.user).values_list('assignment_id', flat=True)
    pending_assignments = Assignment.objects.filter(deadline__gte=now).exclude(id__in=submitted_assignment_ids).order_by('deadline')
    
    # Assignments the student has submitted (to view feedback)
    my_submissions = Submission.objects.filter(student=request.user).order_by('-submitted_at')
    
    # Find peer submissions that need reviewing (not the student's own, and not already reviewed by them)
    reviewed_submission_ids = PeerReview.objects.filter(reviewer=request.user).values_list('submission_id', flat=True)
    submissions_to_review = Submission.objects.exclude(student=request.user).exclude(id__in=reviewed_submission_ids).order_by('?')[:3] # Show up to 3 random submissions

    context = {
        'pending_assignments': pending_assignments,
        'my_submissions': my_submissions,
        'submissions_to_review': submissions_to_review,
        'now': now
    }
    return render(request, 'core/student_dashboard.html', context)

@login_required
def create_assignment(request):
    if not request.user.is_teacher:
        return redirect('dashboard')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        deadline = request.POST.get('deadline')
        
        if title and description and deadline:
            Assignment.objects.create(
                title=title,
                description=description,
                deadline=deadline,
                created_by=request.user
            )
            messages.success(request, 'Assignment created successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fill all fields.')
            
    return render(request, 'core/create_assignment.html')

@login_required
def view_submissions(request, assignment_id):
    if not request.user.is_teacher:
        return redirect('dashboard')
        
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    submissions = assignment.submissions.annotate(review_count=Count('peer_reviews')).order_by('-submitted_at')
    
    context = {
        'assignment': assignment,
        'submissions': submissions
    }
    return render(request, 'core/view_submissions.html', context)

@login_required
def view_peer_reviews(request, submission_id):
    if not request.user.is_teacher:
        return redirect('dashboard')
        
    submission = get_object_or_404(Submission, id=submission_id)
    # Ensure the teacher viewing this is the one who created the assignment
    if submission.assignment.created_by != request.user:
        return redirect('dashboard')
        
    reviews = submission.peer_reviews.all().order_by('-created_at')
    
    context = {
        'submission': submission,
        'reviews': reviews
    }
    return render(request, 'core/view_peer_reviews.html', context)

@login_required
def submit_assignment(request, assignment_id):
    if not request.user.is_student:
        return redirect('dashboard')
        
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if timezone.now() > assignment.deadline:
        messages.error(request, 'The deadline for this assignment has passed.')
        return redirect('dashboard')
        
    if Submission.objects.filter(assignment=assignment, student=request.user).exists():
        messages.warning(request, 'You have already submitted this assignment.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        content = request.POST.get('content')
        file = request.FILES.get('file')
        
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
            messages.error(request, 'Submission must include either text content or a file upload.')
            
    context = {
        'assignment': assignment
    }
    return render(request, 'core/submit_assignment.html', context)

@login_required
def review_submission(request, submission_id):
    if not request.user.is_student:
        return redirect('dashboard')
        
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Prevent reviewing own assignment
    if submission.student == request.user:
        messages.error(request, 'You cannot review your own submission.')
        return redirect('dashboard')
        
    # Prevent multiple reviews
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
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PeerReviewForm()
            
    context = {
        'submission': submission,
        'form': form
    }
    return render(request, 'core/review_submission.html', context)

@login_required
def grade_submission(request, submission_id):
    if not request.user.is_teacher:
        return redirect('dashboard')
        
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Ensure the teacher viewing this is the one who created the assignment
    if submission.assignment.created_by != request.user:
        messages.error(request, 'You do not have permission to grade this submission.')
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = GradeSubmissionForm(request.POST)
        if form.is_valid():
            submission.teacher_grade = form.cleaned_data['teacher_grade']
            submission.teacher_remarks = form.cleaned_data.get('teacher_remarks', '')
            submission.save()
            messages.success(request, 'Official grade submitted successfully!')
            return redirect('view_submissions', assignment_id=submission.assignment.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GradeSubmissionForm()
            
    context = {
        'submission': submission,
        'form': form
    }
    return render(request, 'core/grade_submission.html', context)


class CustomPasswordResetView(PasswordResetView):
    """View for password reset form"""
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Password'
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """View shown after password reset email is sent"""
    template_name = 'registration/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reset Email Sent'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """View for user to set new password"""
    form_class = CustomSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Set New Password'
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """View shown after password has been reset"""
    template_name = 'registration/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Password Reset Complete'
        return context


@login_required
def user_profile(request):
    """Display user profile with statistics"""
    user = request.user
    
    if user.is_student:
        # Student profile statistics
        submissions_count = Submission.objects.filter(student=user).count()
        reviews_given = PeerReview.objects.filter(reviewer=user).count()
        avg_grade = Submission.objects.filter(student=user, teacher_grade__isnull=False).aggregate(Avg('teacher_grade'))['teacher_grade__avg']
        
        # Recent activity
        recent_submissions = Submission.objects.filter(student=user).order_by('-submitted_at')[:5]
        
        context = {
            'submissions_count': submissions_count,
            'reviews_given': reviews_given,
            'avg_grade': round(avg_grade, 2) if avg_grade else 'N/A',
            'recent_submissions': recent_submissions,
            'page_title': 'My Profile',
        }
        return render(request, 'core/student_profile.html', context)
    
    elif user.is_teacher:
        # Teacher profile statistics
        assignments_created = Assignment.objects.filter(created_by=user).count()
        total_submissions = Submission.objects.filter(assignment__created_by=user).count()
        avg_class_grade = Submission.objects.filter(assignment__created_by=user, teacher_grade__isnull=False).aggregate(Avg('teacher_grade'))['teacher_grade__avg']
        
        context = {
            'assignments_created': assignments_created,
            'total_submissions': total_submissions,
            'avg_class_grade': round(avg_class_grade, 2) if avg_class_grade else 'N/A',
            'page_title': 'My Profile',
        }
        return render(request, 'core/teacher_profile.html', context)


@login_required
def student_progress(request):
    """Show student progress dashboard with advanced statistics"""
    if not request.user.is_student:
        return redirect('dashboard')
    
    user = request.user
    
    # Get all submissions for this student
    submissions = Submission.objects.filter(student=user).select_related('assignment')
    
    # Calculate statistics
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(teacher_grade__isnull=False).count()
    avg_grade = submissions.filter(teacher_grade__isnull=False).aggregate(Avg('teacher_grade'))['teacher_grade__avg']
    total_reviews_received = sum(s.peer_reviews.count() for s in submissions)
    avg_peer_grade = PeerReview.objects.filter(submission__student=user).aggregate(Avg('grade'))['grade__avg']
    reviews_given = PeerReview.objects.filter(reviewer=user).count()
    
    # Grade distribution
    grades = list(submissions.filter(teacher_grade__isnull=False).values_list('teacher_grade', flat=True))
    
    context = {
        'total_submissions': total_submissions,
        'graded_submissions': graded_submissions,
        'avg_grade': round(avg_grade, 2) if avg_grade else 0,
        'total_reviews_received': total_reviews_received,
        'avg_peer_grade': round(avg_peer_grade, 2) if avg_peer_grade else 'N/A',
        'reviews_given': reviews_given,
        'submissions': submissions,
        'grades_json': json.dumps(grades),
        'page_title': 'My Progress',
    }
    return render(request, 'core/student_progress.html', context)


@login_required
def notifications(request):
    """Display user notifications"""
    user = request.user
    user_notifications = Notification.objects.filter(user=user).order_by('-created_at')
    unread_count = user_notifications.filter(is_read=False).count()
    
    # Mark all as read
    if request.method == 'POST':
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
    
    context = {
        'notifications': user_notifications,
        'unread_count': unread_count,
        'page_title': 'Notifications',
    }
    return render(request, 'core/notifications.html', context)


@login_required
def grade_statistics(request):
    """Show grade statistics and analysis"""
    user = request.user
    
    if user.is_student:
        # Student's grade statistics
        submissions = Submission.objects.filter(student=user, teacher_grade__isnull=False).select_related('assignment')
        
        stats = {
            'highest_grade': submissions.aggregate(Max=Count('teacher_grade'))['Max'] if submissions else 'N/A',
            'lowest_grade': submissions.aggregate(Min=Count('teacher_grade'))['Min'] if submissions else 'N/A',
            'avg_grade': submissions.aggregate(Avg('teacher_grade'))['teacher_grade__avg'],
            'total_graded': submissions.count(),
        }
        
        context = {
            'submissions': submissions,
            'stats': stats,
            'page_title': 'Grade Statistics',
        }
        return render(request, 'core/student_grade_stats.html', context)
    
    elif user.is_teacher:
        # Teacher's class statistics
        assignments = Assignment.objects.filter(created_by=user)
        
        class_stats = {}
        for assignment in assignments:
            submissions = Submission.objects.filter(assignment=assignment, teacher_grade__isnull=False)
            if submissions.exists():
                avg = submissions.aggregate(Avg('teacher_grade'))['teacher_grade__avg']
                class_stats[assignment.title] = {
                    'avg_grade': round(avg, 2),
                    'submission_count': submissions.count(),
                    'graded_count': submissions.count(),
                }
        
        context = {
            'assignments': assignments,
            'class_stats': class_stats,
            'page_title': 'Grade Statistics',
        }
        return render(request, 'core/teacher_grade_stats.html', context)


# ============ NEW FEATURE VIEWS ============

@login_required
def grade_trends(request):
    """Display grade trends and improvement analysis"""
    if not request.user.is_student:
        return redirect('dashboard')
    
    user = request.user
    submissions = Submission.objects.filter(student=user, teacher_grade__isnull=False).select_related('assignment').order_by('submitted_at')
    
    # Calculate trend
    grades = list(submissions.values_list('teacher_grade', flat=True))
    trend_direction = "Improving" if len(grades) > 1 and grades[-1] > grades[0] else "Declining" if len(grades) > 1 and grades[-1] < grades[0] else "Stable"
    
    context = {
        'submissions': submissions,
        'grades': grades,
        'trend_direction': trend_direction,
        'page_title': 'Grade Trends',
    }
    return render(request, 'core/grade_trends.html', context)


@login_required
def assignment_rubric(request, assignment_id):
    """Display assignment rubric"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    try:
        rubric = assignment.rubric
    except:
        rubric = None
    
    context = {
        'assignment': assignment,
        'rubric': rubric,
        'page_title': f'{assignment.title} - Rubric',
    }
    return render(request, 'core/assignment_rubric.html', context)


@login_required
def create_rubric(request, assignment_id):
    """Create or edit assignment rubric"""
    if not request.user.is_teacher:
        messages.error(request, 'Only teachers can create rubrics.')
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id, created_by=request.user)
    
    if request.method == 'POST':
        try:
            rubric, created = AssignmentRubric.objects.get_or_create(
                assignment=assignment,
                defaults={
                    'title': request.POST.get('title', assignment.title + ' Rubric'),
                    'description': request.POST.get('description', ''),
                    'total_points': int(request.POST.get('total_points', 100))
                }
            )
            messages.success(request, 'Rubric created successfully!')
            return redirect('assignment_rubric', assignment_id=assignment_id)
        except Exception as e:
            messages.error(request, f'Error creating rubric: {str(e)}')
    
    context = {
        'assignment': assignment,
        'page_title': f'Create Rubric for {assignment.title}',
    }
    return render(request, 'core/create_rubric.html', context)


@login_required
def peer_review_quality(request):
    """View peer review quality metrics"""
    if not request.user.is_student:
        return redirect('dashboard')
    
    # Reviews given quality
    reviews_given = PeerReview.objects.filter(reviewer=request.user).prefetch_related('quality_metric')
    
    # Calculate average quality
    quality_metrics = ReviewQualityMetric.objects.filter(review__reviewer=request.user)
    avg_quality = quality_metrics.aggregate(Avg('overall_quality'))['overall_quality__avg'] or 0
    
    context = {
        'reviews_given': reviews_given,
        'avg_quality': round(avg_quality, 2),
        'page_title': 'Your Review Quality',
    }
    return render(request, 'core/peer_review_quality.html', context)


@login_required
def feedback_analytics(request, submission_id):
    """View detailed feedback analytics for a submission"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permission
    if request.user != submission.student and request.user != submission.assignment.created_by:
        messages.error(request, 'You do not have permission to view this.')
        return redirect('dashboard')
    
    # Get all peer reviews
    peer_reviews = submission.peer_reviews.all()
    
    # Get feedback summary
    try:
        feedback_summary = submission.feedback_summary
    except:
        feedback_summary = None
    
    context = {
        'submission': submission,
        'peer_reviews': peer_reviews,
        'feedback_summary': feedback_summary,
        'total_reviews': peer_reviews.count(),
        'page_title': 'Feedback Analytics',
    }
    return render(request, 'core/feedback_analytics.html', context)


@login_required
def performance_insights(request):
    """Display personalized performance insights"""
    if not request.user.is_student:
        return redirect('dashboard')
    
    insights = PerformanceInsight.objects.filter(student=request.user).select_related('assignment').order_by('-generated_at')[:10]
    
    # Categorize insights
    improvements = insights.filter(insight_type='improvement')
    struggles = insights.filter(insight_type='struggling')
    excellent = insights.filter(insight_type='excellent')
    
    context = {
        'insights': insights,
        'improvements': improvements,
        'struggles': struggles,
        'excellent': excellent,
        'page_title': 'Performance Insights',
    }
    return render(request, 'core/performance_insights.html', context)


@login_required
def class_analytics(request):
    """Teacher dashboard with class-wide analytics"""
    if not request.user.is_teacher:
        return redirect('dashboard')
    
    # Get all analytics for teacher's assignments
    analytics = ClassAnalytics.objects.filter(teacher=request.user).select_related('assignment').order_by('-generated_at')
    
    # Calculate overall statistics
    overall_stats = {
        'total_assignments': analytics.count(),
        'average_class_grade': analytics.aggregate(Avg('average_grade'))['average_grade__avg'] or 0,
        'average_submission_rate': analytics.aggregate(Avg('submission_rate'))['submission_rate__avg'] or 0,
    }
    
    context = {
        'analytics': analytics,
        'overall_stats': overall_stats,
        'page_title': 'Class Analytics',
    }
    return render(request, 'core/class_analytics.html', context)


@login_required
def revision_tracking(request, submission_id):
    """Track submission revisions and improvements"""
    submission = get_object_or_404(Submission, id=submission_id)
    
    # Check permission
    if request.user != submission.student and request.user != submission.assignment.created_by:
        messages.error(request, 'You do not have permission to view this.')
        return redirect('dashboard')
    
    revisions = RevisionSubmission.objects.filter(original_submission=submission).order_by('revision_number')
    
    # Calculate improvement
    improvements = []
    if revisions.exists():
        for revision in revisions:
            if revision.grade and submission.teacher_grade:
                improvement = revision.grade - submission.teacher_grade
                improvements.append(improvement)
    
    context = {
        'submission': submission,
        'revisions': revisions,
        'improvements': improvements,
        'page_title': 'Revision Tracking',
    }
    return render(request, 'core/revision_tracking.html', context)


@login_required
def deadline_reminders(request):
    """View upcoming deadline reminders"""
    if not request.user.is_student:
        return redirect('dashboard')
    
    reminders = DeadlineReminder.objects.filter(student=request.user).select_related('assignment').order_by('assignment__deadline')
    
    context = {
        'reminders': reminders,
        'page_title': 'Deadline Reminders',
    }
    return render(request, 'core/deadline_reminders.html', context)

