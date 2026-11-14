(function () {
  const selector = document.getElementById('language');
  const output = document.getElementById('console');
  const status = document.getElementById('language-status');
  const editorHost = document.getElementById('editor');
  const starters = {
    python: '# Write your solution here\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n',
    c: '#include <stdio.h>\n\nint main(void) {\n    // Write your solution here\n    return 0;\n}\n',
    cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your solution here\n    return 0;\n}\n',
    java: 'import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        // Write your solution here\n    }\n}\n'
  };
  let editor = null;
  let source = editorHost.textContent.trim();
  const initial = starters[portalConfig.initialLanguage] ? portalConfig.initialLanguage : 'python';
  selector.value = initial;
  const label = () => selector.options[selector.selectedIndex].text;
  const showLanguage = () => { status.textContent = `Current: ${label()}`; };
  showLanguage();
  selector.addEventListener('change', function () {
    if (editor) {
      const before = editor.getValue();
      monaco.editor.setModelLanguage(editor.getModel(), selector.value);
      if (before === '# Write your solution here' || Object.values(starters).includes(before)) editor.setValue(starters[selector.value]);
    }
    showLanguage();
    output.textContent = `Language changed to ${label()}. Run and Submit will use ${label()}.`;
  });
  const currentCode = () => editor ? editor.getValue() : source;
  const call = async (action) => {
    output.textContent = 'Working…';
    try {
      const response = await fetch(`/api/question/${portalConfig.questionId}/${action}/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': portalConfig.csrf}, body: JSON.stringify({source_code: currentCode(), language: selector.value})});
      const data = await response.json();
      if (action === 'run') {
        output.textContent = `Language: ${label()}\nStatus: ${data.status}\nOutput: ${data.output || '(none)'}\nExpected: ${data.expected_output || '(none)'}\nError: ${data.error || '(none)'}\nTime: ${data.time || '(n/a)'}`;
      } else {
        output.textContent = `${data.result}\nLanguage: ${label()}\nHidden tests passed: ${data.tests_passed}/${data.tests_total}\nScore: ${data.score}\nTotal execution time: ${data.total_execution_time || 0} s\nEstimated time complexity: ${data.time_complexity || 'Unavailable'}\n${data.complexity_note || ''}`;
        const passedAll = data.tests_total > 0 && data.tests_passed === data.tests_total;
        document.getElementById('resultTitle').textContent = passedAll ? 'Congratulations! 🎉' : 'Submission received';
        document.getElementById('resultBody').innerHTML = passedAll
          ? `<p class="lead text-success">All hidden test cases passed.</p><p><b>Score:</b> ${data.score}<br><b>Execution time:</b> ${data.total_execution_time || 0} s<br><b>Estimated time complexity:</b> ${data.time_complexity || 'Unavailable'}</p><p class="small text-muted">${data.complexity_note || ''}</p>`
          : `<p>Your solution was saved.</p><p><b>Hidden tests passed:</b> ${data.tests_passed}/${data.tests_total}<br><b>Score:</b> ${data.score}<br><b>Execution time:</b> ${data.total_execution_time || 0} s<br><b>Estimated time complexity:</b> ${data.time_complexity || 'Unavailable'}</p><p class="small text-muted">${data.complexity_note || ''}</p>`;
        document.getElementById('completionPopup').classList.add('open');
      }
    } catch (error) { output.textContent = `Request failed: ${error.message}`; }
  };
  document.getElementById('run').addEventListener('click', () => call('run'));
  document.getElementById('submit').addEventListener('click', () => call('submit'));
  const closePopup = () => document.getElementById('completionPopup').classList.remove('open');
  document.getElementById('closePopup').addEventListener('click', closePopup);
  document.getElementById('stayOnQuestion').addEventListener('click', closePopup);
  setInterval(() => fetch(`/api/question/${portalConfig.questionId}/log/`, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': portalConfig.csrf}, body: JSON.stringify({source_code: currentCode()})}), portalConfig.interval * 1000);
  if (typeof require !== 'function') { output.textContent = 'Editor library is loading. Please refresh if it does not appear.'; return; }
  require.config({paths: {vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs'}});
  require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(editorHost, {value: source || starters[initial], language: selector.value, theme: 'vs-dark', automaticLayout: true});
  }, function () { output.textContent = 'The code editor could not load. Check your internet connection and refresh.'; });
}());
