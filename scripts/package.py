"""Validate distribution metadata and build skill/plugin ZIPs (standard library only)."""
import argparse
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins' / 'confluence-docs'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate(tag=None):
    manifest = read_json(PLUGIN / 'plugin.json')
    companion = read_json(PLUGIN / '.claude-plugin' / 'plugin.json')
    if (manifest['name'], manifest['version']) != (companion['name'], companion['version']):
        raise ValueError('Claude and portable manifest names/versions must match')
    if not re.fullmatch(r'\d+\.\d+\.\d+', manifest['version']):
        raise ValueError('Version must be a stable major.minor.patch version')
    if tag is not None and tag != 'v' + manifest['version']:
        raise ValueError('Release tag does not match plugin version')
    for path in [ROOT / '.claude-plugin/marketplace.json', ROOT / '.agents/plugins/marketplace.json']:
        catalog = read_json(path)
        for entry in catalog['plugins']:
            source = entry['source']
            relative = source if isinstance(source, str) else source['path']
            target = (ROOT / relative).resolve()
            if not relative.startswith('./') or not target.is_relative_to(ROOT) or not target.is_dir():
                raise ValueError(f'Invalid source path: {relative}')
            if read_json(target / 'plugin.json')['name'] != entry['name']:
                raise ValueError('Marketplace name and manifest name differ')
    for skill in (PLUGIN / 'skills').iterdir():
        text = (skill / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        if not match:
            raise ValueError('Missing skill frontmatter')
        fields = dict(line.split(': ', 1) for line in match[1].splitlines())
        if fields['name'] != skill.name or not fields.get('description'):
            raise ValueError('Invalid skill metadata')
        for relative in re.findall(r'\]\(((?:references|scripts|assets)/[^)]+)\)', text):
            if not (skill / relative).is_file():
                raise ValueError(f'Missing skill resource: {relative}')
    return manifest['version']


def archive_folder(folder, destination):
    tracked = subprocess.check_output(
        ['git', 'ls-files', '-z'], cwd=ROOT
    ).decode('utf-8').split('\0')
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(name for name in tracked if name):
            path = ROOT / relative
            if '.confluence-docs' in path.parts or path.name == 'confluence-docs.config.json':
                continue
            if path.is_file() and path.is_relative_to(folder):
                archive.write(path, path.relative_to(folder.parent).as_posix())
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        expected = folder.name + ('/SKILL.md' if folder.name == 'confluence-doc-writer' else '/plugin.json')
        if expected not in archive.namelist():
            raise ValueError('Package entrypoint is missing; stage new distribution files with git add first')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag')
    args = parser.parse_args()
    version = validate(args.tag)
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    archive_folder(PLUGIN / 'skills/confluence-doc-writer', output / 'confluence-doc-writer.zip')
    archive_folder(PLUGIN, output / 'confluence-docs-plugin.zip')
    print(f'Validated and packaged version {version}')


if __name__ == '__main__':
    main()
