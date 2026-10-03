"""Check generated HTML fragments locally; not a Confluence compatibility test.

Uses only Python's standard library, reads files without modifying them, and
requires explicit closing tags for generated non-void elements. This is a
document output check, not a general-purpose HTML sanitizer.
"""
import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED = set('p h2 h3 h4 h5 h6 strong em b i s del sup sub span div blockquote ul ol li dl dt dd table thead tbody tfoot tr th td caption a pre code figure figcaption img br hr'.split())
VOID = {'img', 'br', 'hr'}
FORBIDDEN = {'html', 'head', 'body', 'title', 'meta', 'style', 'script', 'main', 'h1'}
BLOCKS = set('p h2 h3 h4 h5 h6 div blockquote ul ol dl table pre figure hr'.split())


def normalized_url(value):
    # HTMLParser already decodes attribute entities. Remove controls and spaces
    # before recognizing executable or local schemes, including split schemes.
    return re.sub(r'[\x00-\x20\x7f]', '', value)


class BodyChecker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []
        self.issues = []
        self.has_content = False

    def issue(self, code, message):
        self.issues.append(dict(line=self.getpos()[0], code=code, message=message))

    def handle_decl(self, decl):
        self.issue('document_wrapper', 'DOCTYPE/document declarations are not allowed')

    def unknown_decl(self, data):
        self.issue('declaration', 'Unexpected declaration in body fragment')

    def handle_pi(self, data):
        self.issue('declaration', 'Processing instructions are not allowed')

    def handle_comment(self, data):
        self.issue('comment', 'Remove authoring comments from the final fragment')

    def handle_starttag(self, tag, attrs):
        self.has_content = True
        if tag in FORBIDDEN:
            self.issue('document_wrapper', f'<{tag}> is excluded from the body output')
        elif tag not in ALLOWED:
            self.issue('unsupported_tag', f'<{tag}> is outside the basic output tag set')
        if 'p' in self.stack and tag in BLOCKS:
            self.issue('nesting', 'A block element cannot be nested inside a generated paragraph')
        seen = set()
        for name, value in attrs:
            if name in seen:
                self.issue('attribute', 'Duplicate attribute')
            seen.add(name)
            if name.startswith('on') or name == 'srcdoc':
                self.issue('active_content', 'Event handlers/srcdoc are excluded')
            if name in {'href', 'src'}:
                value = normalized_url(value or '')
                parsed = urlsplit(value)
                scheme = parsed.scheme.casefold()
                if scheme in {'javascript', 'vbscript', 'data', 'file'}:
                    self.issue('url', 'Executable/data/local-file URL is excluded')
                if tag == 'img' and name == 'src':
                    attachment = value.startswith(('/download/attachments/', '/wiki/download/attachments/'))
                    if not value or not ((scheme in {'http', 'https'} and parsed.netloc) or attachment):
                        self.issue('image_path', 'Use a confirmed attachment URL, not a local image path')
        if tag == 'img' and ('src' not in seen or 'alt' not in seen):
            self.issue('image_attribute', 'Images need src and alt attributes')
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.issue('closing_tag', 'Use an explicit closing tag for non-void HTML elements')
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag in VOID:
            self.issue('closing_tag', f'Void element <{tag}> has a closing tag')
        elif not self.stack or self.stack[-1] != tag:
            self.issue('closing_tag', f'Mismatched closing tag </{tag}>')
            if tag in self.stack:
                self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]
        else:
            self.stack.pop()

    def handle_data(self, data):
        if data.strip():
            self.has_content = True
        if '<' in data:
            self.issue('escape', 'Escape literal angle brackets or finish the incomplete HTML tag')
        # Literal template examples/code fences in code are intentional content.
        if 'code' not in self.stack and 'pre' not in self.stack:
            if re.search(r'\{\{[^{}]+\}\}', data):
                self.issue('placeholder', 'Unfilled template placeholder outside code')
            if re.search(r'(?m)^\s*(?:```|~~~)', data):
                self.issue('code_fence', 'Markdown fence outside HTML code/pre')

    def handle_entityref(self, name):
        self.has_content = True

    def handle_charref(self, name):
        self.has_content = True


def validate_html(source):
    checker = BodyChecker()
    try:
        checker.feed(source)
        if '<' in checker.rawdata:
            checker.issue('escape', 'Incomplete HTML markup at the end of the fragment')
        checker.close()
    except ValueError:
        checker.issue('parse', 'Invalid HTML attribute or declaration')
    if checker.stack:
        checker.issue('closing_tag', 'Unclosed elements: ' + ', '.join(checker.stack))
    if not checker.has_content:
        checker.issue('empty', 'Body fragment is empty')
    return checker.issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args(argv)
    failed = False
    for path in args.files:
        try:
            issues = validate_html(path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError) as error:
            print(f'ERROR: {path}: {error}', file=sys.stderr)
            failed = True
            continue
        if issues:
            failed = True
            for issue in issues:
                print(f"ERROR: {path}:{issue['line']} [{issue['code']}] {issue['message']}", file=sys.stderr)
        else:
            print(f'PASS: {path}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
