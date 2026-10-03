"""Observable preview/copy, cross-format comparison and before/after reports."""
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'plugins/confluence-docs/skills/confluence-doc-writer/scripts'
sys.path.insert(0, str(SCRIPTS))
content = importlib.import_module('document_content')
compare = importlib.import_module('compare_documents')
changes = importlib.import_module('summarize_changes')
preview = importlib.import_module('build_preview')
NODE = os.environ.get('CONFLUENCE_TEST_NODE') or shutil.which('node')


class OutputWorkflowTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / 'dist/test-work'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)

    def write(self, name, source):
        path = self.root / name
        path.write_text(source, encoding='utf-8')
        return path

    def run_tool(self, name, *args):
        return subprocess.run([sys.executable, '-X', 'utf8', str(SCRIPTS / name), *map(str, args)], capture_output=True, text=True, encoding='utf-8')

    def test_content_matches_tables_lists_code_links_and_escaped_literals(self):
        body = self.write('doc.body.html', '''<h2>안건 A</h2>
<p><strong>확인된</strong> &amp; 결과와 <code>batch_time</code>.</p>
<ul><li>작업 1<ul><li>하위 작업</li></ul></li><li>작업 2</li></ul>
<table><thead><tr><th>항목</th><th>내용</th></tr></thead><tbody>
<tr><td>A | B</td><td>담당: 김<br>기한: 금요일</td></tr></tbody></table>
<p><a href="https://example.test/a_(b)?x=1&amp;y=2">자료</a></p>
<pre><code>x = "&lt;body&gt;"\nprint(x)</code></pre>
<p>그림 삽입 위치: 확인된 흐름</p><p>흐름 설명</p>''')
        markdown = self.write('doc.md', '''# 페이지 제목

## 안건 A

**확인된** & 결과와 `batch_time`.

- 작업 1
  - 하위 작업
- 작업 2

| 항목 | 내용 |
| --- | --- |
| A \\| B | 담당: 김<br>기한: 금요일 |

[자료](https://example.test/a_(b)?x=1&y=2)

```python
x = "<body>"
print(x)
```

![확인된 흐름](diagrams/flow.png)

흐름 설명
''')
        self.assertTrue(compare.compare(body, markdown)['match'])
        self.assertEqual(self.run_tool('compare_documents.py', body, markdown).returncode, 0)

    def test_changed_table_cells_number_unit_decision_link_and_code_fail(self):
        source = '<h2>효과</h2><p>9월에 15초로 감소했다. 결정은 보류다.</p><table><tr><td>담당</td><td>김</td></tr></table><p><a href="https://example.test/a">자료</a></p><pre><code>x = 1</code></pre>'
        body = self.write('doc.body.html', source)
        base = '# 제목\n\n## 효과\n\n9월에 15초로 감소했다. 결정은 보류다.\n\n| 담당 | 김 |\n| --- | --- |\n\n[자료](https://example.test/a)\n\n```\nx = 1\n```\n'
        self.assertTrue(compare.compare(body, self.write('doc.md', base))['match'])
        for old, new in [('15초', '10초'), ('15초', '15분'), ('보류', '승인'), ('| 담당 | 김 |', '| 김 | 담당 |'), ('/a)', '/b)'), ('x = 1', 'x = 2')]:
            with self.subTest(change=new):
                markdown = self.write('doc.md', base.replace(old, new))
                original = markdown.read_bytes()
                result = self.run_tool('compare_documents.py', body, markdown)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertFalse(json.loads(result.stdout)['match'])
                self.assertEqual(markdown.read_bytes(), original)

    def test_incomplete_unsupported_and_preview_input_not_false_passed(self):
        body = self.write('doc.body.html', '<p>내용</p>')
        for source in ['```python\nx = 1', '[자료][ref]\n\n[ref]: https://example.test', '    x = 1']:
            result = self.run_tool('compare_documents.py', body, self.write('doc.md', source))
            self.assertEqual(result.returncode, 2)
        wrapped = self.write('doc.preview.html', '<html><body><p>내용</p></body></html>')
        self.assertEqual(self.run_tool('compare_documents.py', wrapped, self.write('doc.md', '내용')).returncode, 2)
        merged = '<table><tr><td colspan="2">내용</td></tr></table>'
        with self.assertRaises(content.ContentError):
            content.parse_document(merged, 'html')

    def test_markdown_code_pipe_and_technical_underscore_preserved(self):
        body = '<table><tr><td>표현</td><td>값</td></tr><tr><td><code>a|b</code></td><td>batch_time</td></tr></table>'
        markdown = '| 표현 | 값 |\n| --- | --- |\n| `a|b` | batch_time |'
        left = content.parse_document(body, 'html')
        right = content.parse_document(markdown, 'md')
        self.assertEqual([b.key for b in left], [b.key for b in right])

    def test_heading_hash_entities_caption_and_nested_tables(self):
        body = '<h2>C#</h2><p>A &amp; B</p><table><caption>9월 결과</caption><tr><td>15초</td></tr></table>'
        markdown = '## C#\n\nA &amp; B\n\n9월 결과\n\n| 15초 |\n| --- |'
        left = content.parse_document(body, 'html')
        right = content.parse_document(markdown, 'md')
        self.assertEqual([b.key for b in left], [b.key for b in right])
        self.assertNotEqual([b.key for b in left], [b.key for b in content.parse_document(markdown.replace('9월 결과\n\n', ''), 'md')])
        with self.assertRaises(content.ContentError):
            content.parse_document('<table><tr><td><div><table><tr><td>값</td></tr></table></div></td></tr></table>', 'html')

    def test_change_report_has_added_changed_deleted_content_and_preserves_inputs(self):
        before = self.write('before.md', '# 보고\n\n## 효과\n\n처리시간 20초.\n\n## 삭제 항목\n\n기존 작업.\n')
        after = self.write('after.md', '# 보고\n\n## 효과\n\n처리시간 15초.\n\n## 새 항목\n\n새 작업.\n')
        originals = [p.read_bytes() for p in (before, after)]
        report = self.root / 'after.changes.md'
        result = self.run_tool('summarize_changes.py', before, after, '--output', report)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = report.read_text(encoding='utf-8')
        self.assertIn('20초', output)
        self.assertIn('15초', output)
        self.assertIn('삭제 항목', output)
        self.assertIn('새 항목', output)
        self.assertEqual(originals, [p.read_bytes() for p in (before, after)])
        # Isolated inserts and deletions are classified distinctly.
        extra = self.write('extra.md', after.read_text(encoding='utf-8') + '\n추가 문장.\n')
        self.assertIn('| 추가 |', changes.change_report(after, extra))
        self.assertIn('| 삭제 |', changes.change_report(extra, after))

    def test_change_report_title_and_literal_table_text_without_inferred_reasons(self):
        before = self.write('before.md', '# 이전 제목\n\n## 안건\n\n`<body>`와 A \\| B.\n')
        after = self.write('after.md', '# 새 제목\n\n## 안건\n\n`<body>`와 A \\| C.\n')
        report = changes.change_report(before, after)
        self.assertIn('이전 제목', report)
        self.assertIn('새 제목', report)
        self.assertIn('&lt;body&gt;', report)
        self.assertIn('A \\| B', report)
        self.assertNotIn('효율', report)

    def test_change_report_cannot_overwrite_or_invent_original(self):
        before = self.write('before.md', '# 제목\n\n내용\n')
        original = before.read_bytes()
        self.assertEqual(self.run_tool('summarize_changes.py', before, before, '--output', self.root / 'changes.md').returncode, 2)
        after = self.write('after.md', '# 제목\n\n새 내용\n')
        self.assertEqual(self.run_tool('summarize_changes.py', before, after, '--output', before).returncode, 2)
        self.assertEqual(before.read_bytes(), original)
        self.assertEqual(self.run_tool('summarize_changes.py', self.root / 'missing.md', after, '--output', self.root / 'changes.md').returncode, 2)

    def test_preview_payload_is_original_fragment_and_body_file_is_unchanged(self):
        source = '\n<p data-note="</script>">한글 &amp; &lt;body&gt; \\ 경로</p>\n<pre><code>line 1\n  line 2</code></pre>\n'
        body = self.write('doc.body.html', source)
        original = body.read_bytes()
        output = self.root / 'doc.preview.html'
        result = self.run_tool('build_preview.py', body, '--title', '검토 <제목>', '--output', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        page = output.read_text(encoding='utf-8')
        payload = re.search(r'<script id="body-source" type="application/json">(.*?)</script>', page, re.S)[1]
        self.assertNotIn('<', payload)
        self.assertEqual(json.loads(payload), source)
        self.assertIn('검토 &lt;제목&gt;', page)
        self.assertEqual(body.read_bytes(), original)
        self.assertNotIn('copy-source', body.read_text(encoding='utf-8'))

    def test_preview_rejects_invalid_body_and_overwrite(self):
        body = self.write('doc.body.html', '<p>내용</p>')
        self.assertEqual(self.run_tool('build_preview.py', body, '--title', '제목', '--output', body).returncode, 2)
        invalid = self.write('invalid.body.html', '<body><p>내용</p></body>')
        output = self.root / 'invalid.preview.html'
        self.assertEqual(self.run_tool('build_preview.py', invalid, '--title', '제목', '--output', output).returncode, 2)
        self.assertFalse(output.exists())

    @unittest.skipUnless(NODE, 'Node is needed only for development-side clipboard handler tests')
    def test_copy_handler_uses_exact_source_and_permission_failure_selects_source(self):
        source = '\n<h2>한글 &amp; 결과</h2><p>본문</p>\n'
        page = self.write('doc.preview.html', preview.preview(source, '제목'))
        for mode in ('success', 'rejected', 'unavailable'):
            with self.subTest(mode=mode):
                result = subprocess.run([NODE, str(ROOT / 'tests/preview_controls.cjs'), str(page), mode], capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
