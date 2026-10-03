"""Read generated HTML/Markdown into comparable content blocks; standard library.

Supports the skill's ordinary headings, paragraphs, lists, pipe tables, fenced
code and inline formatting. This is not a complete CommonMark implementation or
a fact checker. Page titles and image URLs are format-specific during comparison.
"""
import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path


class ContentError(ValueError):
    pass


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in {'br', 'hr', 'img'}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {'br', 'hr', 'img'}:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise ContentError(f'Mismatched HTML closing tag: {tag}')
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def handle_comment(self, data):
        raise ContentError('Authoring comments are not final document content')


def tree(source):
    parser = TreeParser()
    parser.feed(source)
    parser.close()
    if len(parser.stack) != 1 or parser.rawdata:
        raise ContentError('Incomplete HTML content')
    return parser.root


def raw_text(node):
    if isinstance(node, str):
        return node
    if node.tag == 'img':
        return ''
    if node.tag in {'br', 'hr'}:
        return '\n'
    value = ''.join(raw_text(child) for child in node.children)
    if node.tag == 'a' and node.attrs.get('href'):
        value += ' [href=' + node.attrs['href'] + ']'
    if node.tag in {'p', 'li', 'ul', 'ol', 'div'}:
        value += '\n'
    return value


def text(node):
    return re.sub(r'\s+', ' ', raw_text(node)).strip()


def balanced(source, start, opening, closing):
    depth, index = 1, start + 1
    while index < len(source):
        char = source[index]
        if char == '\\':
            index += 2
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return source[start + 1:index], index + 1
        index += 1
    return None


INLINE_TAG = re.compile(r'</?(?:br|strong|em|b|i|s|del|sup|sub|span|code|a|img)\b[^>]*>', re.I)


def inline(source):
    """Render the supported inline syntax only, for local content extraction."""
    output, index = [], 0
    while index < len(source):
        char = source[index]
        if char == '&':
            entity = re.match(r'&(?:#[xX][0-9a-fA-F]+|#\d+|[A-Za-z][A-Za-z0-9]+);', source[index:])
            if entity:
                output.append(html.escape(html.unescape(entity[0])))
                index += len(entity[0])
                continue
        if char == '\\' and index + 1 < len(source) and source[index + 1] in r'\`*_{}[]()#+-.!|>~':
            output.append(html.escape(source[index + 1]))
            index += 2
            continue
        if char == '`':
            run = re.match(r'`+', source[index:]).group()
            end = source.find(run, index + len(run))
            if end >= 0:
                value = source[index + len(run):end].replace('\n', ' ')
                if value.startswith(' ') and value.endswith(' ') and value.strip():
                    value = value[1:-1]
                output.append('<code>' + html.escape(value) + '</code>')
                index = end + len(run)
                continue
        image = source.startswith('![', index)
        bracket = index + 1 if image else index
        if source[bracket:bracket + 1] == '[':
            label = balanced(source, bracket, '[', ']')
            if label and source[label[1]:label[1] + 1] == '(':
                target = balanced(source, label[1], '(', ')')
                if target:
                    match = re.fullmatch(r'(<[^>]*>|\S+?)(?:\s+(?:"[^"]*"|\x27[^\x27]*\x27))?', target[0].strip())
                    if not match:
                        raise ContentError('Unsupported Markdown link destination')
                    url = match[1].strip('<>')
                    if not image:
                        output.append('<a href="' + html.escape(url, quote=True) + '">' + inline(label[0]) + '</a>')
                    index = target[1]
                    continue
        if char == '<':
            tag = INLINE_TAG.match(source, index)
            if tag:
                output.append(tag.group())
                index = tag.end()
                continue
            link = re.match(r'<(https?://[^<>\s]+)>', source[index:])
            if link:
                value = html.escape(link[1], quote=True)
                output.append('<a href="' + value + '">' + value + '</a>')
                index += len(link[0])
                continue
        found = False
        for marker, tag in (('**', 'strong'), ('__', 'strong'), ('~~', 's'), ('*', 'em'), ('_', 'em')):
            if not source.startswith(marker, index):
                continue
            if marker.startswith('_') and index and source[index - 1].isalnum():
                continue
            end = source.find(marker, index + len(marker))
            if end > index + len(marker) and not source[index + len(marker)].isspace() and not source[end - 1].isspace():
                if marker.startswith('_') and end + len(marker) < len(source) and source[end + len(marker)].isalnum():
                    continue
                output.append('<' + tag + '>' + inline(source[index + len(marker):end]) + '</' + tag + '>')
                index = end + len(marker)
                found = True
                break
        if not found:
            output.append(html.escape(char))
            index += 1
    return ''.join(output)


def pipe_cells(line):
    line = line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|') and len(re.search(r'\\*$', line[:-1]).group()) % 2 == 0:
        line = line[:-1]
    cells, current, index, code = [], [], 0, ''
    while index < len(line):
        char = line[index]
        if char == '\\' and index + 1 < len(line):
            current.extend(line[index:index + 2])
            index += 2
            continue
        if char == '`':
            run = re.match(r'`+', line[index:]).group()
            if not code:
                code = run
            elif code == run:
                code = ''
            current.append(run)
            index += len(run)
            continue
        if char == '|' and not code:
            cells.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1
    cells.append(''.join(current).strip())
    return cells


HEADING = re.compile(r'^ {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$')
FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})(.*)$')
ITEM = re.compile(r'^( *)([-+*]|\d+[.)])\s+(.+)$')


def table_start(lines, index):
    return (index + 1 < len(lines) and '|' in lines[index]
            and all(re.fullmatch(r':?-{3,}:?', cell) for cell in pipe_cells(lines[index + 1])))


def markdown_html(source):
    lines, output, index = source.splitlines(), [], 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if re.search(r'\[[^]]+\]\[[^]]*\]|\[\^', line) or re.match(r'^\s*\[[^]]+\]:', line):
            raise ContentError('Reference links/footnotes need manual comparison')
        if line.startswith('    ') and not ITEM.match(line):
            raise ContentError('Use fenced code; indented code needs manual comparison')
        fence = FENCE.match(line)
        if fence:
            marker, body = fence[1], []
            index += 1
            while index < len(lines) and not re.fullmatch(r' {0,3}' + re.escape(marker[0]) + '{' + str(len(marker)) + r',}\s*', lines[index]):
                body.append(lines[index])
                index += 1
            if index == len(lines):
                raise ContentError('Unclosed Markdown code fence')
            output.append('<pre><code>' + html.escape('\n'.join(body)) + '</code></pre>')
            index += 1
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading[1])
            output.append(f'<h{level}>' + inline(heading[2]) + f'</h{level}>')
            index += 1
            continue
        if table_start(lines, index):
            header = pipe_cells(line)
            if len(header) != len(pipe_cells(lines[index + 1])):
                raise ContentError('Markdown table header/separator widths differ')
            rows = [header]
            index += 2
            while index < len(lines) and lines[index].strip() and '|' in lines[index]:
                row = pipe_cells(lines[index])
                if len(row) != len(header):
                    raise ContentError('Markdown table row widths differ; escape literal pipes')
                rows.append(row)
                index += 1
            output.append('<table>' + ''.join('<tr>' + ''.join('<td>' + inline(cell) + '</td>' for cell in row) + '</tr>' for row in rows) + '</table>')
            continue
        item = ITEM.match(line)
        if item:
            # Lists become explicit flat item nodes with depth/ordering metadata.
            items, indents = [], []
            while index < len(lines) and (item := ITEM.match(lines[index])):
                indent = len(item[1])
                while indents and indent < indents[-1]:
                    indents.pop()
                if not indents or indent > indents[-1]:
                    indents.append(indent)
                value = item[3]
                index += 1
                while index < len(lines) and lines[index].strip() and not (ITEM.match(lines[index]) or HEADING.match(lines[index]) or FENCE.match(lines[index]) or table_start(lines, index)):
                    value += ' ' + lines[index].strip()
                    index += 1
                ordered = item[2][0].isdigit()
                items.append(f'<item depth="{len(indents) - 1}" ordered="{int(ordered)}">' + inline(value) + '</item>')
            output.append('<list>' + ''.join(items) + '</list>')
            continue
        if re.fullmatch(r'\s*(?:-{3,}|\*{3,}|_{3,})\s*', line):
            index += 1
            continue
        if line.startswith('>'):
            values = []
            while index < len(lines) and lines[index].startswith('>'):
                values.append(lines[index].lstrip('>').strip())
                index += 1
            output.append('<p>' + inline(' '.join(values)) + '</p>')
            continue
        if re.match(r'^\s*<(?:table|ul|ol|pre|p|h[1-6]|div|blockquote|figure)\b', line, re.I):
            values = [line]
            index += 1
            while index < len(lines) and lines[index].strip():
                values.append(lines[index])
                index += 1
            output.append('\n'.join(values))
            continue
        values = [line]
        index += 1
        while index < len(lines) and lines[index].strip() and not (HEADING.match(lines[index]) or FENCE.match(lines[index]) or ITEM.match(lines[index]) or table_start(lines, index)):
            values.append(lines[index])
            index += 1
        output.append('<p>' + inline(' '.join(values)) + '</p>')
    return '\n'.join(output)


@dataclass(frozen=True)
class Block:
    kind: str
    value: object
    section: str

    @property
    def key(self):
        return self.kind, self.value


def content_blocks(root, keep_title=False):
    blocks, headings = [], []

    def add(kind, value):
        blocks.append(Block(kind, value, ' > '.join(title for _, title in headings) or '(문서 시작)'))

    def list_items(node, depth=0):
        result = []
        for child in node.children:
            if not isinstance(child, Node) or child.tag != 'li':
                continue
            own = Node('span', children=[c for c in child.children if not isinstance(c, Node) or c.tag not in {'ul', 'ol'}])
            result.append((depth, int(node.tag == 'ol'), text(own)))
            for nested in child.children:
                if isinstance(nested, Node) and nested.tag in {'ul', 'ol'}:
                    result.extend(list_items(nested, depth + 1))
        return result

    def walk(node):
        for child in node.children:
            if isinstance(child, str):
                if child.strip():
                    add('text', text(child))
                continue
            tag = child.tag
            if re.fullmatch(r'h[1-6]', tag):
                level, title = int(tag[1]), text(child)
                if level == 1 and not keep_title:
                    if blocks or headings:
                        raise ContentError('Only the initial Markdown page title may be excluded')
                    continue
                while headings and headings[-1][0] >= level:
                    headings.pop()
                headings.append((level, title))
                add('heading', (level, title))
            elif tag in {'p', 'figcaption', 'caption'}:
                value = text(child)
                if value and not value.startswith('그림 삽입 위치:'):
                    add('text', value)
            elif tag == 'pre':
                value = raw_text(child).replace('\r\n', '\n').rstrip('\n')
                add('code', value)
            elif tag == 'table':
                rows = []

                for caption in child.children:
                    if isinstance(caption, Node) and caption.tag == 'caption' and text(caption):
                        add('text', text(caption))

                def nested_table(parent):
                    return any(isinstance(c, Node) and (c.tag == 'table' or nested_table(c)) for c in parent.children)

                def cells(parent):
                    for row in parent.children:
                        if not isinstance(row, Node):
                            continue
                        if row.tag == 'tr':
                            values = []
                            for cell in row.children:
                                if not isinstance(cell, Node) or cell.tag not in {'th', 'td'}:
                                    continue
                                if cell.attrs.get('rowspan', '1') != '1' or cell.attrs.get('colspan', '1') != '1':
                                    raise ContentError('Merged table cells need manual comparison')
                                if nested_table(cell):
                                    raise ContentError('Nested tables need manual comparison')
                                values.append(text(cell))
                            rows.append(tuple(values))
                        else:
                            cells(row)

                cells(child)
                if rows and len({len(row) for row in rows}) != 1:
                    raise ContentError('HTML table row widths differ')
                add('table', tuple(rows))
            elif tag in {'ul', 'ol'}:
                add('list', tuple(list_items(child)))
            elif tag == 'list':
                add('list', tuple((int(c.attrs['depth']), int(c.attrs['ordered']), text(c)) for c in child.children if isinstance(c, Node)))
            elif tag in {'img', 'hr'}:
                continue
            else:
                walk(child)

    walk(root)
    return blocks


def parse_document(source, format, keep_title=False):
    if format == 'html':
        from validate_body import validate_html
        issues = validate_html(source)
        if issues:
            raise ContentError('Invalid body HTML: ' + ', '.join(issue['code'] for issue in issues))
        return content_blocks(tree(source), keep_title=keep_title)
    if format == 'md':
        return content_blocks(tree(markdown_html(source)), keep_title=keep_title)
    raise ContentError('Only .md and body .html inputs are supported')


def read_document(path, keep_title=False):
    path = Path(path)
    format = {'.md': 'md', '.html': 'html'}.get(path.suffix.casefold())
    return parse_document(path.read_text(encoding='utf-8-sig'), format, keep_title=keep_title)
