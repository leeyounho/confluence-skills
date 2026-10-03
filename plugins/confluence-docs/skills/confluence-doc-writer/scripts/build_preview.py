"""Build an offline preview with a button that copies the original HTML fragment."""
import argparse
import html
import json
import sys
from pathlib import Path

from validate_body import validate_html


CONTROLS = r'''
const source = JSON.parse(document.getElementById('body-source').textContent);
const sourceBox = document.getElementById('source-box');
const sourcePanel = document.getElementById('source-panel');
const status = document.getElementById('copy-status');
sourceBox.value = source;
function selectSource() {
  sourcePanel.open = true;
  sourceBox.focus();
  sourceBox.select();
  sourceBox.setSelectionRange(0, sourceBox.value.length);
}
document.getElementById('select-source').addEventListener('click', selectSource);
document.getElementById('copy-source').addEventListener('click', async () => {
  try {
    if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('clipboard unavailable');
    await navigator.clipboard.writeText(source);
    status.textContent = '본문 HTML 소스를 복사했습니다. Confluence HTML 소스 입력 창에 붙여넣으세요.';
  } catch (_) {
    selectSource();
    status.textContent = '자동 복사를 사용할 수 없습니다. 선택된 소스를 Ctrl+C 또는 Cmd+C로 복사하세요.';
  }
});
'''


def preview(source, title):
    issues = validate_html(source)
    if issues:
        raise ValueError('Invalid body HTML: ' + ', '.join(issue['code'] for issue in issues))
    # Escaping '<' prevents document/code content from ending this script element.
    payload = json.dumps(source, ensure_ascii=True).replace('<', '\\u003c')
    safe_title = html.escape(title, quote=True)
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title} — 미리보기</title>
<style>
body {{ margin: 0; color: #172b4d; background: #f4f5f7; font: 16px/1.6 system-ui, sans-serif; }}
header, main, details {{ max-width: 1080px; margin: 20px auto; padding: 20px; background: white; border-radius: 8px; }}
h1 {{ margin: 0 0 10px; font-size: 25px; }}
button {{ margin: 4px 8px 4px 0; padding: 10px 16px; border: 1px solid #0052cc; border-radius: 4px; background: #0052cc; color: white; cursor: pointer; font: inherit; }}
button:focus-visible {{ outline: 3px solid #ffab00; outline-offset: 2px; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #dfe1e6; padding: 8px 10px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }}
th {{ background: #f4f5f7; }}
pre {{ overflow: auto; padding: 12px; background: #f4f5f7; }}
img {{ max-width: 100%; height: auto; }}
textarea {{ box-sizing: border-box; width: 100%; min-height: 240px; margin-top: 12px; font: 14px/1.5 monospace; }}
#copy-status {{ min-height: 1.6em; }}
@media (max-width: 700px) {{ header, main, details {{ margin: 8px; padding: 12px; }} main {{ overflow-x: auto; }} }}
</style>
</head>
<body>
<header>
<h1>{safe_title}</h1>
<p>제목은 Confluence 제목 필드에 입력하고, 아래 버튼으로 본문 HTML 소스를 복사하세요.</p>
<button id="copy-source" type="button">본문 HTML 소스 복사</button>
<button id="select-source" type="button">소스 선택</button>
<p id="copy-status" role="status" aria-live="polite"></p>
</header>
<main id="document-preview">
{source}
</main>
<details id="source-panel"><summary>복사할 본문 HTML 소스</summary><textarea id="source-box" readonly aria-label="본문 HTML 소스"></textarea></details>
<script id="body-source" type="application/json">{payload}</script>
<script>{CONTROLS}</script>
</body>
</html>
'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('body_html', type=Path)
    parser.add_argument('--title', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() == args.body_html.resolve():
            raise ValueError('Preview must not overwrite the body fragment')
        source = args.body_html.read_text(encoding='utf-8-sig')
        args.output.write_text(preview(source, args.title), encoding='utf-8')
        print(f'WROTE: {args.output}')
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
