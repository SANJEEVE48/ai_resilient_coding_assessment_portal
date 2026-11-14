from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    FACULTY, STUDENT = 'faculty', 'student'
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[(FACULTY, 'Faculty'), (STUDENT, 'Student')], default=STUDENT)
    def __str__(self): return f'{self.user.username} ({self.role})'

class Assessment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.PositiveIntegerField(help_text='Minutes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessments')
    assigned_students = models.ManyToManyField(User, blank=True, related_name='assigned_assessments')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title

class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    title = models.CharField(max_length=200)
    problem_statement = models.TextField()
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)
    constraints = models.TextField(blank=True)
    marks = models.PositiveIntegerField(default=10)
    allowed_languages = models.CharField(max_length=100, default='c,cpp,python,java')
    time_limit = models.PositiveIntegerField(default=2, help_text='Seconds')
    memory_limit = models.PositiveIntegerField(default=128, help_text='MB')
    def __str__(self): return self.title

class TestCase(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='test_cases')
    input = models.TextField(blank=True)
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)

class Submission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    source_code = models.TextField()
    language = models.CharField(max_length=20)
    score = models.FloatField(default=0)
    manual_score = models.FloatField(null=True, blank=True)
    tests_passed = models.PositiveIntegerField(default=0)
    tests_total = models.PositiveIntegerField(default=0)
    ai_review = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(auto_now=True)
    class Meta: unique_together = ('student', 'question')

    @property
    def effective_score(self):
        return self.manual_score if self.manual_score is not None else self.score

class CodeLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    source_code = models.TextField()
    line_count = models.PositiveIntegerField()
    added_function = models.CharField(max_length=150, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    class Meta: ordering = ['timestamp']

class ExecutionLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    language = models.CharField(max_length=20)
    status = models.CharField(max_length=100)
    output = models.TextField(blank=True)
    error = models.TextField(blank=True)
    execution_time = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
