from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Assessment, Question, Submission, TestCase

class AssessmentForm(forms.ModelForm):
    assigned_students = forms.ModelMultipleChoiceField(queryset=User.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = Assessment
        fields = ['title', 'description', 'duration', 'assigned_students', 'is_published']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_students'].queryset = User.objects.filter(profile__role='student')

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        exclude = ['assessment']
        widgets = {'problem_statement': forms.Textarea(attrs={'rows': 5}), 'input_format': forms.Textarea(attrs={'rows': 2}), 'output_format': forms.Textarea(attrs={'rows': 2}), 'constraints': forms.Textarea(attrs={'rows': 2})}

class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = ['question']
        widgets = {'input': forms.Textarea(attrs={'rows': 2}), 'expected_output': forms.Textarea(attrs={'rows': 2})}

class ManualEvaluationForm(forms.ModelForm):
    manual_score = forms.FloatField(min_value=0, required=False, label='Manual marks')

    class Meta:
        model = Submission
        fields = ['manual_score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manual_score'].max_value = self.instance.question.marks
        self.fields['manual_score'].widget.attrs.update({'step': '0.1', 'max': self.instance.question.marks})

class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=[('student', 'Student'), ('faculty', 'Faculty')])
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password1', 'password2']
