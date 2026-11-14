import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Assessment, Question, Submission, TestCase as CodingTestCase


class AIReviewViewTests(TestCase):
    def setUp(self):
        self.faculty = User.objects.create_user(username='faculty', password='test-pass')
        self.faculty.profile.role = 'faculty'
        self.faculty.profile.save()
        self.student = User.objects.create_user(username='student', password='test-pass')
        assessment = Assessment.objects.create(
            title='Test assessment',
            description='Assessment description',
            duration=30,
            created_by=self.faculty,
        )
        self.question = Question.objects.create(
            assessment=assessment,
            title='Sum two integers',
            problem_statement='Read two integers and print their sum.',
            input_format='Two integers',
            output_format='Their sum',
            constraints='Integers fit in 32 bits',
            marks=10,
        )
        CodingTestCase.objects.create(
            question=self.question,
            input='secret hidden input',
            expected_output='secret expected output',
            is_hidden=True,
        )
        self.submission = Submission.objects.create(
            student=self.student,
            question=self.question,
            source_code='print(sum(map(int, input().split())))',
            language='python',
            score=4,
            tests_passed=2,
            tests_total=5,
        )

    @override_settings(
        AI_REVIEW_PROVIDER='ollama',
        AI_REVIEW_OLLAMA_URL='http://127.0.0.1:11434/api/chat',
        AI_REVIEW_MODEL='test-model',
    )
    @patch('assessments.ai_review.requests.post')
    def test_faculty_can_store_review_without_changing_mark(self, post):
        response = Mock()
        response.json.return_value = {
            'message': {
                'content': json.dumps({
                        'summary': 'The approach is sound.',
                        'logic_review': 'It parses two values and adds them.',
                        'likely_issues': ['Check malformed input handling.'],
                        'complexity': 'O(1)',
                        'confidence': 'medium',
                        'suggested_score': 7,
                }),
            },
        }
        post.return_value = response
        self.client.force_login(self.faculty)

        result = self.client.post(reverse('request_ai_review', args=[self.submission.id]))

        self.assertRedirects(result, f'/faculty/evaluation/?submission={self.submission.id}')
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.ai_review['suggested_score'], 7)
        self.assertEqual(self.submission.score, 4)
        self.assertIsNone(self.submission.manual_score)
        self.assertEqual(post.call_args.args[0], 'http://127.0.0.1:11434/api/chat')
        self.assertEqual(post.call_args.kwargs['headers'], {})
        self.assertEqual(post.call_args.kwargs['json']['format'], 'json')
        sent_evidence = json.loads(post.call_args.kwargs['json']['messages'][1]['content'])
        self.assertEqual(sent_evidence['hidden_tests_passed'], 2)
        self.assertNotIn('secret hidden input', json.dumps(sent_evidence))
        self.assertNotIn('secret expected output', json.dumps(sent_evidence))

    def test_student_cannot_request_ai_review(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse('request_ai_review', args=[self.submission.id]))
        self.assertEqual(response.status_code, 404)

    @override_settings(AI_REVIEW_PROVIDER='openai', AI_REVIEW_API_KEY='')
    def test_evaluation_page_shows_provider_setup_when_cloud_key_is_missing(self):
        self.client.force_login(self.faculty)
        response = self.client.get(reverse('evaluation'), {'submission': self.submission.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI logic review')
        self.assertContains(response, 'AI review unavailable')
