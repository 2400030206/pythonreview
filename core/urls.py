from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Password Reset Views
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # User Profile Views
    path('profile/', views.user_profile, name='profile'),
    path('progress/', views.student_progress, name='student_progress'),
    path('notifications/', views.notifications, name='notifications'),
    path('grade-statistics/', views.grade_statistics, name='grade_statistics'),
    
    # New Feature Views (Advanced Academic)
    path('grade-trends/', views.grade_trends, name='grade_trends'),
    path('assignment/<int:assignment_id>/rubric/', views.assignment_rubric, name='assignment_rubric'),
    path('assignment/<int:assignment_id>/create-rubric/', views.create_rubric, name='create_rubric'),
    path('peer-review-quality/', views.peer_review_quality, name='peer_review_quality'),
    path('submission/<int:submission_id>/feedback-analytics/', views.feedback_analytics, name='feedback_analytics'),
    path('performance-insights/', views.performance_insights, name='performance_insights'),
    path('class-analytics/',views.class_analytics, name='class_analytics'),
    path('submission/<int:submission_id>/revision-tracking/', views.revision_tracking, name='revision_tracking'),
    path('deadline-reminders/', views.deadline_reminders, name='deadline_reminders'),
    
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Teacher Views
    path('assignment/create/', views.create_assignment, name='create_assignment'),
    path('assignment/<int:assignment_id>/submissions/', views.view_submissions, name='view_submissions'),
    path('submission/<int:submission_id>/reviews/', views.view_peer_reviews, name='view_peer_reviews'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),

    # Student Views
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/review/', views.review_submission, name='review_submission'),
]
