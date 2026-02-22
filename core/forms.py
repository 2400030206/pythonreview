from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from .models import User, PeerReview, Submission

class UserRegistrationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        widget=forms.RadioSelect, 
        initial='student',
        help_text="Select your role in the system.",
        label="Role"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
                'placeholder': 'johndoe',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
                'placeholder': 'john@example.com',
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style password1 field
        self.fields['password1'].widget = forms.PasswordInput(attrs={
            'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
            'placeholder': 'Enter password',
            'required': True,
        })
        
        # Style password2 field
        self.fields['password2'].widget = forms.PasswordInput(attrs={
            'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
            'placeholder': 'Confirm password',
            'required': True,
        })

    def save(self, commit=True):
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


class PeerReviewForm(forms.ModelForm):
    """Form for creating peer reviews with proper validation"""
    
    class Meta:
        model = PeerReview
        fields = ['feedback', 'grade']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide constructive feedback for your peer. Be helpful and respectful.',
                'required': True
            }),
            'grade': forms.NumberInput(attrs={
                'class': 'form-control',
                'type': 'number',
                'min': '1',
                'max': '100',
                'placeholder': 'Enter grade (1-100)',
                'required': True
            })
        }

    def clean_grade(self):
        grade = self.cleaned_data.get('grade')
        if grade is not None:
            if not isinstance(grade, int) or not (1 <= grade <= 100):
                raise forms.ValidationError('Grade must be an integer between 1 and 100.')
        return grade

    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback')
        if feedback and len(feedback.strip()) < 10:
            raise forms.ValidationError('Feedback must be at least 10 characters long.')
        return feedback


class GradeSubmissionForm(forms.Form):
    """Form for teachers to grade student submissions"""
    teacher_grade = forms.IntegerField(
        label='Grade',
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'type': 'number',
            'min': '1',
            'max': '100',
            'placeholder': 'Enter grade (1-100)',
            'required': True
        })
    )
    teacher_remarks = forms.CharField(
        label='Remarks',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Provide additional remarks or feedback for the student.',
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Form for users to request password reset"""
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
            'autocomplete': 'email',
            'placeholder': 'Enter your email address',
            'required': True,
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email


class CustomSetPasswordForm(SetPasswordForm):
    """Form for users to set a new password"""
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
            'placeholder': 'Enter new password',
            'required': True,
            'autocomplete': 'new-password',
        })
        
        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'class': 'mt-1 appearance-none rounded relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-brand-500 focus:border-brand-500 sm:text-sm',
            'placeholder': 'Confirm password',
            'required': True,
            'autocomplete': 'new-password',
        })
