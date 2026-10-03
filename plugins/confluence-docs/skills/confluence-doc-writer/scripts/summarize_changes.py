"""Create a separate content-change report from actual before/after files."""
import argparse
import html
import sys
from pathlib import Path

from compare_documents import differences
from document_content import ContentError, read_document


def literal(value):
    value = html.escape(str(value), quote=False).replace('\\', '\\\\')
    for char in '|`*_[]':
        value = value.replace(char, '\\' + char)
    return value.replace('\n', '<br>')


def describe(block):
    value = block['content']
    if block['kind'] == 'heading':
        return literal(value[1])
    if block['kind'] == 'table':
        return '<br>'.join(' / '.join(literal(cell) for cell in row) for row in value)
    if block['kind'] == 'list':
        return '<br>'.join(literal(item[2]) for item in value)
    return literal(value)


def change_report(before_path, after_path):
    before_path, after_path = Path(before_path), Path(after_path)
    if before_path.resolve() == after_path.resolve():
        raise ContentError('Before and after must be different files')
    if before_path.suffix.casefold() != after_path.suffix.casefold():
        raise ContentError('Before and after must use the same format')
    before = read_document(before_path, keep_title=True)
    after = read_document(after_path, keep_title=True)
    changes = differences(before, after)
    lines = ['# 문서 수정 내역', '', f'- 이전: {literal(before_path.name)}', f'- 이후: {literal(after_path.name)}', '',
             '본문 내용 기준으로 비교했다. 서식만의 변경과 이미지 경로는 비교 대상에서 제외한다.', '']
    if not changes:
        lines.append('비교 대상 내용의 변경이 없다.')
    else:
        lines.extend(['| 구분 | 위치 | 이전 내용 | 변경 내용 |', '| --- | --- | --- | --- |'])
        for change in changes:
            old, new = change['before'], change['after']
            sections = list(dict.fromkeys(b['section'] for b in old + new))
            lines.append('| ' + {'changed': '변경', 'added': '추가', 'deleted': '삭제'}[change['type']] + ' | '
                         + '<br>'.join(literal(s) for s in sections) + ' | '
                         + '<br>'.join(describe(b) for b in old) + ' | '
                         + '<br>'.join(describe(b) for b in new) + ' |')
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in {args.before.resolve(), args.after.resolve()}:
            raise ContentError('The report must not overwrite either input')
        report = change_report(args.before, args.after)
        args.output.write_text(report, encoding='utf-8')
        print(f'WROTE: {args.output}')
        return 0
    except (ContentError, OSError, UnicodeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
