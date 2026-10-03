"""List/select templates and check recorded readiness; Python standard library only.

No files are written. Readiness trusts facts recorded by the caller and does not
prove that the user actually confirmed them; follow references/intake.md first.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
BUILTIN = SKILL / 'assets/templates'
SETTLED = {'confirmed', 'agreed_pending', 'agreed_none'}
STATUSES = SETTLED | {'missing', 'unresolved'}


def normalized(value):
    return re.sub(r'\s+', '', value).casefold()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def load_catalog(folder=BUILTIN):
    catalog = read_json(folder / 'catalog.json')
    if catalog.get('schema_version') != 1:
        raise ValueError('Unsupported template catalog version')
    names = set()
    for entry in catalog['templates']:
        filename = entry['file']
        if Path(filename).name != filename or not (folder / filename).is_file():
            raise ValueError(f'Invalid catalog file: {filename}')
        keys = {normalized(v) for v in [entry['id'], entry['name'], filename, *entry['aliases']]}
        if names & keys:
            raise ValueError('Ambiguous catalog alias')
        names.update(keys)
        sections = entry['sections']
        if len({s['name'] for s in sections}) != len(sections):
            raise ValueError('Duplicate section name')
        for section in sections:
            if section['mode'] not in {'required', 'optional', 'derived'} or not section['criteria']:
                raise ValueError('Invalid section criteria')
    return catalog['templates']


def settings(config_path=None, workspace=None):
    workspace = Path(workspace or Path.cwd())
    path = Path(config_path).resolve() if config_path else workspace / 'confluence-docs.config.json'
    config = read_json(path) if path.is_file() else {}
    if config_path and not path.is_file():
        raise ValueError(f'Config not found: {path}')
    root = Path(config.get('template_root', str(workspace / '.confluence-docs/templates')))
    if not root.is_absolute():
        root = path.parent / root
    aliases = config.get('template_aliases', {})
    if not isinstance(aliases, dict):
        raise ValueError('template_aliases must be an object')
    for filename in aliases.values():
        if not isinstance(filename, str) or '/' in filename or '\\' in filename or Path(filename).suffix not in {'.md', '.html'}:
            raise ValueError('Alias targets must be .md/.html filenames inside template_root')
    return root.resolve(), aliases, config.get('default_template')


def local_files(root):
    return sorted(p for p in root.iterdir() if p.is_file() and p.suffix in {'.md', '.html'}) if root.is_dir() else []


def inventory(root, aliases, catalog=None):
    catalog = catalog if catalog is not None else load_catalog()
    local = [dict(name=p.stem, file=p.name, path=str(p), origin='local',
                  aliases=[key for key, filename in aliases.items() if filename == p.name])
             for p in local_files(root)]
    public = [dict(name=e['name'], id=e['id'], file=e['file'], path=str(BUILTIN / e['file']),
                   origin='builtin', aliases=e['aliases']) for e in catalog]
    return local + public


def select(name, root, aliases, catalog=None, builtin=BUILTIN):
    catalog = catalog if catalog is not None else load_catalog(builtin)
    key = normalized(name)
    files = local_files(root)
    # Explicit local filenames/stems take priority over aliases.
    direct = [p for p in files if key in {normalized(p.name), normalized(p.stem)}]
    alias_targets = {target for alias, target in aliases.items() if normalized(alias) == key}
    if len(direct) > 1 or len(alias_targets) > 1:
        raise ValueError('Ambiguous local template; specify a filename')
    if direct:
        return dict(path=str(direct[0]), origin='local', name=direct[0].stem, sections=None)
    if alias_targets:
        target = root / next(iter(alias_targets))
        if not target.is_file():
            raise ValueError(f'Selected local template not found: {target}')
        return dict(path=str(target), origin='local', name=name, sections=None)
    matches = [e for e in catalog if key in {normalized(v) for v in [e['id'], e['name'], e['file'], *e['aliases']]}]
    if len(matches) != 1:
        raise ValueError('Template not found or ambiguous; list templates or specify a path')
    entry = matches[0]
    override = root / entry['file']
    if override.is_file():
        return dict(path=str(override), origin='local', name=entry['name'], sections=None)
    return dict(entry, path=str(builtin / entry['file']), origin='builtin')


def readiness(template, state):
    sections = template.get('sections')
    if sections is None:
        raise ValueError('Local template: read its own criteria; do not apply builtin criteria automatically')
    records = state.get('sections')
    if not isinstance(records, dict):
        raise ValueError('State must contain a sections object')
    known = {s['name'] for s in sections}
    if set(records) - known:
        raise ValueError('Unknown section in state')
    rows, blockers = [], []
    for section in sections:
        name, mode = section['name'], section['mode']
        record = records.get(name, {})
        if not isinstance(record, dict):
            raise ValueError(f'Section state must be an object: {name}')
        status = record.get('status', 'missing')
        if status not in STATUSES:
            raise ValueError(f'Invalid status for {name}')
        if status in SETTLED and (not isinstance(record.get('content'), str) or not record['content'].strip()):
            raise ValueError(f'Settled section needs content: {name}')
        if mode == 'derived' and status == 'missing':
            display = 'derive_from_confirmed_content'
        elif mode == 'optional' and status == 'missing':
            display = 'omit'
        else:
            display = status
            if status == 'unresolved' or (mode == 'required' and status == 'missing'):
                blockers.append(name)
        rows.append(dict(name=name, mode=mode, status=display, criteria=section['criteria']))
    return dict(ready=not blockers, blockers=blockers, sections=rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', help='Local config; defaults to the working directory config')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--list', action='store_true')
    action.add_argument('--select', metavar='NAME')
    parser.add_argument('--state', help='Read-only readiness JSON, for builtin templates')
    args = parser.parse_args(argv)
    try:
        root, aliases, _ = settings(args.config)
        if args.state and not args.select:
            raise ValueError('--state requires --select')
        result = select(args.select, root, aliases) if args.select else inventory(root, aliases)
        if args.state:
            result = readiness(result, read_json(args.state))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
