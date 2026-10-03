"""Read-only comparison of generated body HTML and editing Markdown."""
import argparse
import json
import sys
from difflib import SequenceMatcher
from pathlib import Path

from document_content import ContentError, read_document


def differences(before, after):
    result = []
    matcher = SequenceMatcher(a=[b.key for b in before], b=[b.key for b in after], autojunk=False)
    for tag, a1, a2, b1, b2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        result.append(dict(type={'replace': 'changed', 'delete': 'deleted', 'insert': 'added'}[tag],
                           before=[dict(kind=b.kind, section=b.section, content=b.value) for b in before[a1:a2]],
                           after=[dict(kind=b.kind, section=b.section, content=b.value) for b in after[b1:b2]]))
    return result


def compare(html_path, markdown_path):
    if Path(html_path).suffix.casefold() != '.html' or Path(markdown_path).suffix.casefold() != '.md':
        raise ContentError('Specify body .html first and editing .md second')
    before, after = read_document(html_path), read_document(markdown_path)
    if not before and not after:
        raise ContentError('No comparable text/table/code; image-only documents need manual comparison')
    result = differences(before, after)
    return dict(match=not result, html_blocks=len(before), markdown_blocks=len(after), differences=result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('body_html', type=Path)
    parser.add_argument('markdown', type=Path)
    args = parser.parse_args(argv)
    try:
        result = compare(args.body_html, args.markdown)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['match'] else 1
    except (ContentError, OSError, UnicodeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
