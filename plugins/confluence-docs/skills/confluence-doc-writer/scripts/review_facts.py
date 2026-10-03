"""Review structured numbers/citations locally; never repair or fetch evidence.

Caller must extract metrics, occurrences and relevant claims from the source and
draft without inventing evidence. Passing this tool does not prove factual truth
or that a citation entails a claim. Such checks require human/model review.
"""
import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from pathlib import Path

KINDS = {'measured', 'qualitative', 'expected'}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Numbers must be decimal strings or finite numeric values')
    text = str(value).strip()
    if not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?', text):
        raise ValueError('Use decimal numbers with optional valid thousands separators')
    result = Decimal(text.replace(',', ''))
    if not result.is_finite() or len(result.as_tuple().digits) > 40 or result.as_tuple().exponent < -12:
        raise ValueError('Number exceeds supported precision')
    return result


def percent_matches(actual, reported):
    claimed = number(reported)
    precision = Decimal(1).scaleb(min(0, claimed.as_tuple().exponent))
    return actual.quantize(precision, rounding=ROUND_HALF_UP) == claimed


def review(data):
    if not isinstance(data, dict):
        raise ValueError('Review input must be an object')
    issues, calculations = [], []

    def issue(code, item, message):
        issues.append(dict(code=code, item=item, message=message))

    sources = {}
    for source in data.get('sources', []):
        key = source['id']
        if key in sources:
            raise ValueError('Duplicate source id')
        sources[key] = source

    def references(item, refs):
        if not isinstance(refs, list) or not refs:
            issue('missing_source', item, '근거 자료 또는 사용자 답변을 연결해 주세요.')
            return
        for ref in refs:
            source = sources.get(ref)
            if source is None:
                issue('unknown_source', item, '연결한 근거 자료를 찾을 수 없습니다.')
            elif not isinstance(source.get('text'), str) or not source['text'].strip():
                issue('source_unavailable', item, '자료 이름만 있어 내용 확인이 필요합니다.')

    metrics = {}
    for metric in data.get('metrics', []):
        key = metric['id']
        if key in metrics:
            raise ValueError('Duplicate metric id')
        metrics[key] = metric
        kind = metric.get('kind')
        if kind not in KINDS:
            issue('metric_kind', key, '실측·정성 평가·기대 효과를 구분해 주세요.')
        references(key, metric.get('source_ids', []))
        for field in ['unit', 'period', 'scope']:
            if not isinstance(metric.get(field), str) or not metric[field].strip():
                issue('missing_context', key, f'{field} 기준을 확인해 주세요.')
        before_unit = metric.get('before_unit', metric.get('unit'))
        after_unit = metric.get('after_unit', metric.get('unit'))
        units_match = isinstance(before_unit, str) and before_unit == after_unit and bool(before_unit.strip())
        if not units_match:
            issue('unit_conflict', key, '전후 단위가 다르거나 없습니다. 같은 기준인지 확인해 주세요.')
        rate = None
        values = {}
        rate_requested = 'reported_percent' in metric or any(o.get('field') == 'reported_percent' for o in metric.get('occurrences', []))
        if 'before' in metric and 'after' in metric:
            try:
                values = {field: number(metric[field]) for field in ['before', 'after']}
                direction = metric.get('direction')
                if direction not in {'decrease', 'increase'}:
                    if rate_requested:
                        issue('direction', key, '감소율인지 증가율인지 확인해 주세요.')
                elif units_match:
                    if values['before'] <= 0 or values['after'] < 0:
                        if rate_requested:
                            issue('percentage_baseline', key, '0·음수 기준의 변화는 비율을 임의 계산하지 않고 표현을 확인합니다.')
                    else:
                        sign = 1 if direction == 'decrease' else -1
                        rate = (values['before'] - values['after']) / values['before'] * 100 * sign
                        calculations.append(dict(id=key, computed_percent=format(rate.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f'), kind=kind))
                        if rate < 0:
                            issue('direction_conflict', key, '전후 값이 지정한 증가·감소 방향과 반대입니다.')
                        if 'reported_percent' in metric and not percent_matches(rate, metric['reported_percent']):
                            issue('percentage_conflict', key, '기재한 변화율과 계산값이 다릅니다. 수정 기준을 확인해 주세요.')
            except (ValueError, InvalidOperation):
                issue('invalid_number', key, '숫자 형식·정밀도 또는 계산 기준을 확인해 주세요.')
        else:
            issue('missing_values', key, '전후 비교값이 부족합니다. 비교 수치를 추측하지 않습니다.')
        for occurrence in metric.get('occurrences', []):
            section = occurrence.get('section', '문서')
            field = occurrence.get('field')
            item = f'{key}:{section}'
            if occurrence.get('unit', metric.get('unit')) != metric.get('unit'):
                issue('occurrence_unit', item, '본문·요약의 단위가 서로 다릅니다.')
            if occurrence.get('period', metric.get('period')) != metric.get('period'):
                issue('occurrence_period', item, '본문·요약의 비교 기간이 서로 다릅니다.')
            if occurrence.get('kind', kind) != kind:
                issue('occurrence_kind', item, '실측·기대 효과 표현이 본문과 요약에서 다릅니다.')
            try:
                if field == 'reported_percent':
                    if rate is None:
                        issue('unverified_percent', item, '변화율을 검증할 전후 값·단위가 부족합니다.')
                    elif not percent_matches(rate, occurrence.get('value')):
                        issue('summary_conflict', item, '문서에 반복된 변화율과 계산값이 다릅니다.')
                elif field in {'before', 'after'}:
                    if field not in values or number(occurrence.get('value')) != values[field]:
                        issue('summary_conflict', item, '문서에 반복된 전후 값이 근거 값과 다릅니다.')
                else:
                    issue('occurrence_field', item, '반복 수치의 before/after/reported_percent 종류를 확인해 주세요.')
            except (ValueError, InvalidOperation):
                issue('invalid_number', item, '문서의 반복 수치 형식을 확인해 주세요.')

    seen_claims = set()
    for claim in data.get('claims', []):
        key = claim['id']
        if key in seen_claims:
            raise ValueError('Duplicate claim id')
        seen_claims.add(key)
        if not isinstance(claim.get('text'), str) or not claim['text'].strip():
            issue('missing_claim', key, '검토할 핵심 주장을 입력해 주세요.')
        references(key, claim.get('source_ids', []))
        if claim.get('kind') not in KINDS:
            issue('claim_kind', key, '주장의 실측·정성 평가·기대 여부를 확인해 주세요.')
        if 'metric_id' in claim:
            linked = metrics.get(claim['metric_id'])
            if linked is None:
                issue('unknown_metric', key, '주장에 연결한 수치를 찾을 수 없습니다.')
            elif linked.get('kind') != claim.get('kind'):
                issue('claim_kind_conflict', key, '연결 수치의 기대 효과를 실제 성과처럼 표현했는지 확인해 주세요.')
        evidence = claim.get('evidence', [])
        if not evidence:
            issue('missing_evidence', key, '근거에서 해당 주장과 관련된 문장을 연결해 주세요.')
        for entry in evidence:
            source = sources.get(entry.get('source_id'))
            quote = entry.get('quote')
            if entry.get('source_id') not in claim.get('source_ids', []):
                issue('evidence_source', key, '근거 문장과 연결 자료의 id가 다릅니다.')
            if source is None or not isinstance(quote, str) or not quote.strip():
                issue('unavailable_evidence', key, '근거 문장이나 자료를 확인할 수 없습니다.')
            elif not isinstance(source.get('text'), str) or quote not in source['text']:
                issue('evidence_not_found', key, '기재한 근거 문장이 제공된 자료에 없습니다.')
    checked = len(metrics) + len(seen_claims)
    if not checked:
        issue('no_items', 'review', '검토할 핵심 주장 또는 수치가 없습니다.')
    return dict(passed=not issues, checked_items=checked, issues=issues, calculations=calculations,
                note='계산·표현·자료 연결 검사입니다. 근거가 주장을 뒷받침하는지는 별도로 읽고 확인하세요.')


def review_document(data):
    with localcontext() as context:
        context.prec = 100
        return review(data)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'))
        result = review_document(data.get('review', data))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['passed'] else 1
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
