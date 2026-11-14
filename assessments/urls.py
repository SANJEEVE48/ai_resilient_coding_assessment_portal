from django.urls import path
from . import views
urlpatterns = [
 path('', views.landing, name='landing'), path('login/', views.role_login, name='login'), path('signup/', views.signup, name='signup'), path('logout/', views.role_logout, name='logout'), path('dashboard/', views.dashboard, name='dashboard'),
 path('faculty/assessment/new/', views.create_assessment, name='create_assessment'), path('faculty/assessment/<int:assessment_id>/', views.assessment_detail, name='assessment_detail'), path('faculty/assessment/<int:assessment_id>/question/new/', views.create_question, name='create_question'), path('faculty/question/<int:question_id>/test/new/', views.create_test, name='create_test'), path('faculty/evaluation/', views.evaluation, name='evaluation'), path('faculty/evaluation/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'), path('faculty/evaluation/<int:submission_id>/ai-review/', views.request_ai_review, name='request_ai_review'),
 path('faculty/assessment/<int:assessment_id>/publish/', views.toggle_publish, name='toggle_publish'),
 path('faculty/assessment/<int:assessment_id>/students/', views.assign_students, name='assign_students'),
 path('faculty/students/', views.manage_students, name='manage_students'), path('faculty/students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
 path('assessment/<int:assessment_id>/', views.student_assessment, name='student_assessment'), path('question/<int:question_id>/code/', views.coding_page, name='coding_page'), path('api/question/<int:question_id>/run/', views.run_code, name='run_code'), path('api/question/<int:question_id>/submit/', views.submit_code, name='submit_code'), path('api/question/<int:question_id>/log/', views.save_log, name='save_log'),
]
