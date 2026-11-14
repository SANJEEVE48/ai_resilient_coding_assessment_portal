import json, re
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import AssessmentForm, ManualEvaluationForm, QuestionForm, TestCaseForm, SignUpForm
from .models import Assessment, Question, TestCase, Submission, CodeLog, ExecutionLog
from .services import execute
from .ai_review import AIReviewError, review_submission

def is_faculty(user): return user.is_authenticated and getattr(user, 'profile', None) and user.profile.role == 'faculty'
def faculty_required(view):
    def wrapped(request, *args, **kwargs):
        if not is_faculty(request.user): raise Http404('Faculty access required')
        return view(request, *args, **kwargs)
    return login_required(wrapped)
def can_access_question(user, question): return is_faculty(user) or question.assessment.assigned_students.filter(pk=user.pk).exists()

def landing(request): return render(request, 'assessments/landing.html')
def role_login(request):
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        role = request.POST.get('role')
        if user and getattr(user, 'profile', None) and user.profile.role == role:
            login(request, user); return redirect('dashboard')
        messages.error(request, 'Invalid credentials or account role.')
    return render(request, 'assessments/login.html')
def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        user.profile.role = form.cleaned_data['role']
        user.profile.save()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'assessments/signup.html', {'form': form})
def role_logout(request): logout(request); return redirect('landing')

@login_required
def dashboard(request):
    if is_faculty(request.user):
        assessments = Assessment.objects.filter(created_by=request.user).annotate(question_count=Count('questions'))
        return render(request, 'assessments/faculty_dashboard.html', {'assessments': assessments})
    assessments = request.user.assigned_assessments.filter(is_published=True).prefetch_related('questions')
    return render(request, 'assessments/student_dashboard.html', {'assessments': assessments})

@faculty_required
def create_assessment(request):
    form = AssessmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        assessment = form.save(commit=False); assessment.created_by = request.user; assessment.save(); form.save_m2m()
        return redirect('assessment_detail', assessment_id=assessment.id)
    return render(request, 'assessments/form.html', {'form': form, 'title': 'Create assessment'})

@faculty_required
def assessment_detail(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id, created_by=request.user)
    questions = list(assessment.questions.all())
    students = list(assessment.assigned_students.all())
    submissions = Submission.objects.filter(question__assessment=assessment).select_related('student', 'question')
    submission_map = {(item.student_id, item.question_id): item for item in submissions}
    log_counts = {(item['student_id'], item['question_id']): item['total'] for item in CodeLog.objects.filter(question__assessment=assessment).values('student_id', 'question_id').annotate(total=Count('id'))}
    performance = []
    for student in students:
        for question in questions:
            submission = submission_map.get((student.id, question.id))
            versions = log_counts.get((student.id, question.id), 0)
            performance.append({'student': student, 'question': question, 'submission': submission, 'versions': versions, 'status': 'Submitted' if submission else ('In progress' if versions else 'Not started')})
    return render(request, 'assessments/assessment_detail.html', {'assessment': assessment, 'performance': performance})

@faculty_required
def toggle_publish(request, assessment_id):
    if request.method != 'POST':
        raise Http404()
    assessment = get_object_or_404(Assessment, pk=assessment_id, created_by=request.user)
    assessment.is_published = not assessment.is_published
    assessment.save(update_fields=['is_published'])
    messages.success(request, f'Assessment is now {"published" if assessment.is_published else "a draft"}.')
    return redirect('assessment_detail', assessment_id=assessment.id)

@faculty_required
def assign_students(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id, created_by=request.user)
    students = User.objects.filter(profile__role='student').order_by('username')
    if request.method == 'POST':
        assessment.assigned_students.set(students.filter(pk__in=request.POST.getlist('students')))
        messages.success(request, 'Student assignments saved.')
        return redirect('assessment_detail', assessment_id=assessment.id)
    return render(request, 'assessments/assign_students.html', {'assessment': assessment, 'students': students})

@faculty_required
def manage_students(request):
    students = User.objects.filter(profile__role='student').annotate(assessment_count=Count('assigned_assessments')).order_by('username')
    return render(request, 'assessments/manage_students.html', {'students': students})

@faculty_required
def delete_student(request, student_id):
    if request.method != 'POST':
        raise Http404()
    student = get_object_or_404(User, pk=student_id, profile__role='student')
    name = student.username
    student.delete()
    messages.success(request, f'Student account "{name}" was deleted.')
    return redirect('manage_students')

@faculty_required
def create_question(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id, created_by=request.user)
    form = QuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        q = form.save(commit=False); q.assessment = assessment; q.save(); return redirect('assessment_detail', assessment_id=assessment.id)
    return render(request, 'assessments/form.html', {'form': form, 'title': 'Add question'})

@faculty_required
def create_test(request, question_id):
    question = get_object_or_404(Question, pk=question_id, assessment__created_by=request.user)
    form = TestCaseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        t = form.save(commit=False); t.question = question; t.save(); return redirect('assessment_detail', assessment_id=question.assessment_id)
    return render(request, 'assessments/form.html', {'form': form, 'title': f'Add test case: {question.title}'})

@login_required
def student_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, pk=assessment_id, is_published=True, assigned_students=request.user)
    return render(request, 'assessments/student_assessment.html', {'assessment': assessment})

@login_required
def coding_page(request, question_id):
    question = get_object_or_404(Question.objects.prefetch_related('test_cases'), pk=question_id)
    if not can_access_question(request.user, question): raise Http404()
    sample = question.test_cases.filter(is_hidden=False).first()
    prior = Submission.objects.filter(student=request.user, question=question).first()
    return render(request, 'assessments/coding.html', {'question': question, 'sample': sample, 'prior': prior, 'interval': settings.CODE_LOG_INTERVAL_SECONDS})

def api_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if not can_access_question(request.user, question): raise Http404()
    try: return question, json.loads(request.body)
    except json.JSONDecodeError: return question, {}

@login_required
def run_code(request, question_id):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    question, data = api_question(request, question_id); sample = question.test_cases.filter(is_hidden=False).first()
    result = execute(data.get('source_code', ''), data.get('language', ''), sample.input if sample else '')
    ExecutionLog.objects.create(student=request.user, question=question, language=data.get('language',''), status=result['status'], output=result.get('output',''), error=result.get('error',''), execution_time=result.get('time',''))
    result['expected_output'] = sample.expected_output if sample else ''
    return JsonResponse(result)

@login_required
def submit_code(request, question_id):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    question, data = api_question(request, question_id)
    tests = question.test_cases.filter(is_hidden=True); passed = 0; execution_times = []
    for test in tests:
        r = execute(data.get('source_code',''), data.get('language',''), test.input)
        try: execution_times.append(float(r.get('time') or 0))
        except (TypeError, ValueError): pass
        if r.get('status') == 'Accepted' and r.get('output','').strip() == test.expected_output.strip(): passed += 1
    total = tests.count(); score = (passed / total * question.marks) if total else 0
    Submission.objects.update_or_create(student=request.user, question=question, defaults={'source_code':data.get('source_code',''), 'language':data.get('language',''), 'score':score, 'tests_passed':passed, 'tests_total':total})
    save_snapshot(request.user, question, data.get('source_code',''))
    return JsonResponse({'tests_passed': passed, 'tests_total': total, 'score': score, 'result': 'Submitted successfully', 'total_execution_time': round(sum(execution_times), 4), 'time_complexity': estimate_complexity(data.get('source_code', '')), 'complexity_note': 'This is a simple estimate based on visible loop nesting; it is not a formal proof.'})

def estimate_complexity(source):
    """Conservative, explainable estimate for demonstration purposes only."""
    lines = source.splitlines()
    max_depth = 0
    loop_indents = []
    for line in lines:
        text = line.strip().lower()
        indent = len(line) - len(line.lstrip())
        while loop_indents and indent <= loop_indents[-1]:
            loop_indents.pop()
        if re.search(r'\b(for|while)\b', text):
            loop_indents.append(indent)
            max_depth = max(max_depth, len(loop_indents))
    if 'sort(' in source.lower() or '.sort' in source.lower():
        return 'O(n log n) — heuristic'
    if max_depth >= 3: return 'O(n³) or higher — heuristic'
    if max_depth == 2: return 'O(n²) — heuristic'
    if max_depth == 1: return 'O(n) — heuristic'
    return 'O(1) — heuristic'

def functions_in(code):
    return set(re.findall(r'(?:def\s+|(?:public|private|static)\s+\w+[\s<>\[\]]*\s+)([A-Za-z_]\w*)\s*\(', code))
def save_snapshot(student, question, source):
    previous = CodeLog.objects.filter(student=student, question=question).last()
    if previous and previous.source_code == source: return None
    old = functions_in(previous.source_code) if previous else set(); new = functions_in(source) - old
    return CodeLog.objects.create(student=student, question=question, source_code=source, line_count=len(source.splitlines()), added_function=', '.join(sorted(new)), metadata={})

@login_required
def save_log(request, question_id):
    if request.method != 'POST': return JsonResponse({'error': 'POST required'}, status=405)
    question, data = api_question(request, question_id)
    log = save_snapshot(request.user, question, data.get('source_code',''))
    return JsonResponse({'saved': bool(log), 'interval': settings.CODE_LOG_INTERVAL_SECONDS})

@faculty_required
def evaluation(request):
    assessments = Assessment.objects.filter(created_by=request.user)
    submission = None; logs = []
    stats = None
    if request.GET.get('submission'):
        submission = get_object_or_404(Submission, pk=request.GET['submission'], question__assessment__created_by=request.user)
        logs = CodeLog.objects.filter(student=submission.student, question=submission.question)
        executions = ExecutionLog.objects.filter(student=submission.student, question=submission.question)
        elapsed = (logs.last().timestamp - logs.first().timestamp).total_seconds() // 60 if logs.count() > 1 else 0
        stats = {'runs': executions.count(), 'compile_errors': executions.exclude(status__in=['Accepted', 'Wrong Answer']).count(), 'minutes': int(elapsed), 'functions': sum(1 for log in logs if log.added_function)}
    submissions = Submission.objects.filter(question__assessment__created_by=request.user).select_related('student','question','question__assessment')
    form = ManualEvaluationForm(instance=submission) if submission else None
    provider = settings.AI_REVIEW_PROVIDER
    ai_review_enabled = provider == 'ollama' or (provider == 'openai' and bool(settings.AI_REVIEW_API_KEY))
    return render(request, 'assessments/evaluation.html', {'assessments': assessments, 'submissions': submissions, 'submission': submission, 'logs': logs, 'stats': stats, 'form': form, 'ai_review_enabled': ai_review_enabled, 'ai_review_provider': provider, 'ai_review_model': settings.AI_REVIEW_MODEL})

@faculty_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id, question__assessment__created_by=request.user)
    if request.method != 'POST':
        raise Http404()
    form = ManualEvaluationForm(request.POST, instance=submission)
    if form.is_valid():
        submission.manual_score = form.cleaned_data['manual_score']
        submission.save(update_fields=['manual_score'])
        messages.success(request, 'Manual marks saved.')
    else:
        messages.error(request, form.errors.get('manual_score', ['Enter a valid mark.'])[0])
    return redirect(f'/faculty/evaluation/?submission={submission.id}')

@faculty_required
def request_ai_review(request, submission_id):
    if request.method != 'POST':
        raise Http404()
    submission = get_object_or_404(Submission, pk=submission_id, question__assessment__created_by=request.user)
    try:
        submission.ai_review = review_submission(submission)
        submission.save(update_fields=['ai_review'])
        messages.success(request, 'AI review generated. Check its evidence and decide the final mark yourself.')
    except AIReviewError as exc:
        messages.error(request, str(exc))
    return redirect(f'/faculty/evaluation/?submission={submission.id}')
