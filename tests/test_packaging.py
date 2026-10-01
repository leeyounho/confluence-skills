"""Verify local/private template files stay out of distribution ZIPs."""
import importlib.util
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('package', Path(__file__).resolve().parents[1] / 'scripts/package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackagingTests(unittest.TestCase):
    def test_private_and_untracked_files_are_excluded_from_both_packages(self):
        original_root = package.ROOT
        temp_parent = original_root / 'dist' / 'test-work'
        temp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent) as temp:
            root = Path(temp).resolve()
            assert root.is_relative_to(temp_parent.resolve()) and root != temp_parent.resolve()
            package.ROOT = root
            try:
                subprocess.run(['git', 'init', '-q', str(root)], check=True)
                plugin = root / 'plugins/confluence-docs'
                skill = plugin / 'skills/confluence-doc-writer'
                files = {
                    plugin / 'plugin.json': '{}',
                    skill / 'SKILL.md': 'Public skill',
                    skill / 'assets/templates/public.md': 'Public template',
                    skill / '.confluence-docs/templates/private.md': 'PRIVATE_TEST_DATA',
                    plugin / 'confluence-docs.config.json': '{"private": true}',
                }
                for path, content in files.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding='utf-8')
                # Even forcibly tracked private paths must not enter the ZIP.
                subprocess.run(['git', 'add', '-f', '.'], cwd=root, check=True)
                (skill / 'untracked-company-notes.md').write_text('PRIVATE_TEST_DATA', encoding='utf-8')
                for folder in [skill, plugin]:
                    destination = root / (folder.name + '.zip')
                    package.archive_folder(folder, destination)
                    with zipfile.ZipFile(destination) as archive:
                        names = archive.namelist()
                        self.assertTrue(any(name.endswith('/assets/templates/public.md') for name in names))
                        self.assertFalse(any('.confluence-docs/' in name for name in names))
                        self.assertFalse(any(name.endswith('confluence-docs.config.json') for name in names))
                        self.assertFalse(any(name.endswith('untracked-company-notes.md') for name in names))
                        self.assertFalse(any(b'PRIVATE_TEST_DATA' in archive.read(name) for name in names))
            finally:
                package.ROOT = original_root


if __name__ == '__main__':
    unittest.main()
