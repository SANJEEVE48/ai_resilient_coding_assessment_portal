from django.contrib import admin
from .models import Profile, Assessment, Question, TestCase, Submission, CodeLog, ExecutionLog
admin.site.register([Profile, Assessment, Question, TestCase, Submission, CodeLog, ExecutionLog])
