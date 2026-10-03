"""Save/resume and arithmetic/evidence behavior, using only fictional local data."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'plugins/confluence-docs/skills/confluence-doc-writer'


def module(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / f'scripts/{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


progress = module('progress')
reviewer = module('review_facts')


def intake_state():
    return {
        'schema_version': 1, 'title': '가상 배치 완료보고',
        'template': {'name': '완료보고', 'origin': 'builtin', 'reference': 'completion-report'},
        'sections': {
            '배경': {'status': 'confirmed', 'content': '배치 대기시간 개선'},
            '효과': {'status': 'unresolved', 'content': '실측인지 기대 효과인지 확인 중'},
        },
        'facts': [{'text': '중복 조회 제거 완료', 'status': 'confirmed', 'source_ids': ['memo']}],
        'pending_questions': ['비교 기간과 측정 범위는 무엇인가요?'],
        'review': {'sources': [], 'metrics': [], 'claims': []},
    }


def review_input():
    return {
        'sources': [{'id': 'memo', 'text': '9월 A 배치 평균 처리시간은 기존 20초에서 15초로 줄었다.'}],
        'metrics': [{
            'id': 'time', 'kind': 'measured', 'before': '20', 'after': '15', 'unit': '초',
            'period': '9월 동일 조건 비교', 'scope': 'A 배치', 'direction': 'decrease',
            'reported_percent': '25', 'source_ids': ['memo'],
            'occurrences': [{'section': 'summary', 'field': 'reported_percent', 'value': '25'}],
        }],
        'claims': [{
            'id': 'effect', 'text': 'A 배치 처리시간 감소', 'kind': 'measured', 'metric_id': 'time',
            'source_ids': ['memo'],
            'evidence': [{'source_id': 'memo', 'quote': '기존 20초에서 15초로 줄었다.'}],
        }],
    }


class ProgressTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / 'dist/test-work'
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.root = Path(self.temp.name).resolve()
        assert self.root.is_relative_to(parent.resolve()) and self.root != parent.resolve()
        self.addCleanup(self.temp.cleanup)
        self.template = self.root / 'completion.md'
        self.template.write_text('# 완료보고\n## 효과\n', encoding='utf-8')

    def test_save_load_preserves_answers_questions_and_review(self):
        state = intake_state()
        original = copy.deepcopy(state)
        path = progress.save(state, self.root, '완료보고', self.template)
        self.assertTrue(path.is_relative_to(self.root / '.confluence-docs/drafts'))
        restored = progress.load(path, self.template)
        self.assertTrue(restored['template_verified'])
        for key in ['sections', 'facts', 'pending_questions', 'review']:
            self.assertEqual(restored['state'][key], state[key])
        self.assertEqual(state, original)

    def test_repeated_save_preserves_old_snapshot_and_list(self):
        state = intake_state()
        first = progress.save(state, self.root, 'report', self.template)
        old_bytes = first.read_bytes()
        state['sections']['효과'] = {'status': 'confirmed', 'content': '실측 시간 감소 확인'}
        second = progress.save(state, self.root, 'report', self.template)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), old_bytes)
        self.assertEqual(len(progress.list_snapshots(self.root)), 2)

    def test_changed_or_missing_template_check_is_not_verified(self):
        path = progress.save(intake_state(), self.root, 'report', self.template)
        self.assertFalse(progress.load(path)['template_verified'])
        self.template.write_text('# 새 양식\n', encoding='utf-8')
        self.assertEqual(progress.load(path, self.template)['template_check'], 'changed')
        self.assertFalse(progress.load(path, self.template)['template_verified'])

    def test_text_line_endings_do_not_force_reconfirmation(self):
        self.template.write_bytes(b'# report\r\n## effect\r\n')
        path = progress.save(intake_state(), self.root, 'report', self.template)
        self.template.write_bytes(b'# report\n## effect\n')
        self.assertTrue(progress.load(path, self.template)['template_verified'])

    def test_invalid_state_and_traversal_name_do_not_write(self):
        with self.assertRaises(ValueError):
            progress.save(intake_state(), self.root, '../escape')
        state = intake_state()
        state['sections']['효과'] = {'status': 'confirmed'}
        with self.assertRaises(ValueError):
            progress.save(state, self.root)
        self.assertFalse((self.root / '.confluence-docs').exists())

    def test_cli_load_is_read_only_and_invalid_version_rejected(self):
        path = progress.save(intake_state(), self.root, 'report', self.template)
        before = path.read_bytes()
        result = subprocess.run([sys.executable, '-X', 'utf8', str(SKILL / 'scripts/progress.py'), '--load', str(path), '--template-file', str(self.template)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout.decode('utf-8'))['template_verified'])
        self.assertEqual(path.read_bytes(), before)
        state = intake_state()
        state['schema_version'] = 2
        with self.assertRaises(ValueError):
            progress.validate_state(state)


class ReviewTests(unittest.TestCase):
    def codes(self, data):
        return {issue['code'] for issue in reviewer.review_document(data)['issues']}

    def test_consistent_arithmetic_evidence_and_input_is_unchanged(self):
        data = review_input()
        before = copy.deepcopy(data)
        result = reviewer.review_document(data)
        self.assertTrue(result['passed'])
        self.assertEqual(result['calculations'][0]['computed_percent'], '25.00')
        self.assertEqual(data, before)

    def test_reported_and_summary_rates_are_checked_independently(self):
        data = review_input()
        data['metrics'][0]['reported_percent'] = '20'
        data['metrics'][0]['occurrences'][0]['value'] = '30'
        self.assertTrue({'percentage_conflict', 'summary_conflict'} <= self.codes(data))

    def test_expected_effect_is_not_presented_as_measured(self):
        data = review_input()
        data['metrics'][0]['kind'] = 'expected'
        data['metrics'][0]['occurrences'][0]['kind'] = 'measured'
        self.assertTrue({'claim_kind_conflict', 'occurrence_kind'} <= self.codes(data))

    def test_units_periods_and_missing_context_need_confirmation(self):
        data = review_input()
        metric = data['metrics'][0]
        metric['after_unit'] = '밀리초'
        metric['occurrences'][0]['period'] = '다른 기간'
        metric.pop('scope')
        self.assertTrue({'unit_conflict', 'occurrence_period', 'missing_context'} <= self.codes(data))

    def test_zero_negative_baselines_and_opposite_direction(self):
        data = review_input()
        for baseline in ['0', '-20']:
            data['metrics'][0]['before'] = baseline
            self.assertIn('percentage_baseline', self.codes(data))
        data['metrics'][0]['before'] = '10'
        self.assertIn('direction_conflict', self.codes(data))

    def test_rounding_respects_displayed_precision_and_valid_thousands(self):
        data = review_input()
        metric = data['metrics'][0]
        metric.update(before='3', after='2', reported_percent='33.3', occurrences=[])
        self.assertNotIn('percentage_conflict', self.codes(data))
        metric.update(before='1,000', after='750', reported_percent='25')
        self.assertNotIn('invalid_number', self.codes(data))
        metric['before'] = '1,00'
        self.assertIn('invalid_number', self.codes(data))

    def test_absolute_change_does_not_require_a_percentage(self):
        data = review_input()
        metric = data['metrics'][0]
        metric.update(before='0', after='10', unit='건', direction='increase', occurrences=[])
        metric.pop('reported_percent')
        data['sources'][0]['text'] = '9월 A 배치 처리량은 0건에서 10건으로 변했다.'
        data['claims'][0]['text'] = 'A 배치 측정값 변화'
        data['claims'][0]['evidence'][0]['quote'] = '0건에서 10건으로 변했다.'
        self.assertTrue(reviewer.review_document(data)['passed'])

    def test_missing_source_or_invented_evidence_is_not_passed(self):
        data = review_input()
        data['claims'][0]['evidence'][0]['quote'] = '50% 개선되었다.'
        self.assertIn('evidence_not_found', self.codes(data))
        data['sources'] = []
        self.assertIn('unknown_source', self.codes(data))

    def test_qualitative_claim_without_fake_measurements(self):
        data = {'sources': [{'id': 'reply', 'text': '실측 없이 운영자가 대기 감소를 체감했다고 답함.'}],
                'claims': [{'id': 'effect', 'kind': 'qualitative', 'text': '운영자 체감 개선',
                            'source_ids': ['reply'], 'evidence': [{'source_id': 'reply', 'quote': '실측 없이 운영자가 대기 감소를 체감'}]}]}
        self.assertTrue(reviewer.review_document(data)['passed'])
        self.assertFalse(reviewer.review_document({})['passed'])

    def test_cli_nonzero_on_conflict_and_does_not_repair_input(self):
        parent = ROOT / 'dist/test-work'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            root = Path(directory).resolve()
            assert root.is_relative_to(parent.resolve()) and root != parent.resolve()
            path = root / 'review.json'
            data = review_input()
            data['metrics'][0]['reported_percent'] = '20'
            path.write_text(json.dumps({'review': data}, ensure_ascii=False), encoding='utf-8')
            original = path.read_bytes()
            result = subprocess.run([sys.executable, '-X', 'utf8', str(SKILL / 'scripts/review_facts.py'), str(path)], capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(path.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
