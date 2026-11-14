import base64, time, requests
from django.conf import settings

LANGUAGES = {'c': 50, 'cpp': 54, 'python': 71, 'java': 62}

def execute(source, language, stdin=''):
    """Execute only through Judge0; never runs student code locally."""
    if language not in LANGUAGES:
        return {'status': 'Unsupported language', 'error': 'Choose an allowed language.'}
    headers = {'Content-Type': 'application/json'}
    if settings.JUDGE0_API_KEY: headers['X-RapidAPI-Key'] = settings.JUDGE0_API_KEY
    try:
        body = {'source_code': base64.b64encode(source.encode()).decode(), 'stdin': base64.b64encode(stdin.encode()).decode(), 'language_id': LANGUAGES[language], 'base64_encoded': True}
        response = requests.post(f'{settings.JUDGE0_URL}/submissions?base64_encoded=true&wait=false', json=body, headers=headers, timeout=15)
        response.raise_for_status(); token = response.json()['token']
        for _ in range(12):
            time.sleep(.5)
            result = requests.get(f'{settings.JUDGE0_URL}/submissions/{token}?base64_encoded=true', headers=headers, timeout=15).json()
            if result.get('status', {}).get('id', 1) > 2: break
        decode = lambda k: base64.b64decode(result[k]).decode(errors='replace') if result.get(k) else ''
        return {'status': result.get('status', {}).get('description', 'Unknown'), 'output': decode('stdout'), 'error': decode('compile_output') or decode('stderr') or decode('message'), 'time': result.get('time') or ''}
    except requests.RequestException as exc:
        return {'status': 'Judge0 unavailable', 'error': str(exc), 'output': '', 'time': ''}
