"""Instructor: python package_release.py v0.2 (writes a ZIP beside this folder)."""
from pathlib import Path
import re
import sys
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parent
version = sys.argv[1] if len(sys.argv) > 1 else 'v0.1'
if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?', version):
    raise SystemExit('Use a version such as v0.2')
target = root.parent / f'class-block-game-{version}.zip'
if target.exists():
    raise SystemExit(f'{target.name} already exists; choose a new version.')
files = [p for p in root.iterdir() if p.is_file() and (p.suffix in {'.py', '.md', '.txt', '.command', '.bat'} or p.name == '.gitignore')]
for directory in ('docs', 'assets', 'tests'):
    files += [p for p in (root / directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != '.DS_Store']
with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, str(Path('class-block-game') / path.relative_to(root)))
print(target)
