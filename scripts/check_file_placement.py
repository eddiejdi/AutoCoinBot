#!/usr/bin/env python3
"""Check and optionally move files to recommended folders.

Usage:
  python scripts/check_file_placement.py [--move] [--yes]

Flags:
  --move    Move misplaced files to suggested folders (use with caution).
  --yes     When used with --move, perform moves without interactive prompt.
"""
import os
import shutil
import argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
IGNORE_DIRS = {'.git', '.venv', 'venv', '.venv_export', '.venv_test', '__pycache__', 'container', 'deploy'}

RULES = [
    # pattern check is simple: extension-based suggestions
    ('.md', 'docs'),
    ('.png', 'docs/reports/images'),
    ('.jpg', 'docs/reports/images'),
    ('.jpeg', 'docs/reports/images'),
    ('.json', 'data'),
    ('.db', 'data'),
    ('.py', 'scripts'),
]

WHITELIST = {
    'README.md', 'AGENTE_TREINAMENTO.md', 'QUICK_START.sh', 'LICENSE'
}


def suggested_target(fname):
    ln = fname.lower()
    for ext, tgt in RULES:
        if ln.endswith(ext):
            return os.path.join(ROOT, tgt)
    return None


def find_root_files():
    files = []
    for entry in os.listdir(ROOT):
        p = os.path.join(ROOT, entry)
        if os.path.isfile(p) and not entry.startswith('.'):
            files.append(entry)
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--move', action='store_true')
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()

    misplaced = []
    for fname in find_root_files():
        if fname in WHITELIST:
            continue
        tgt = suggested_target(fname)
        if tgt:
            # if the file is already inside the target (rare for root scan), skip
            # we only scan root-level files here
            misplaced.append((fname, tgt))

    if not misplaced:
        print('No misplaced root files detected.')
        return 0

    print('Found files recommended to be moved:')
    for f, t in misplaced:
        print(f' - {f} -> {os.path.relpath(t, ROOT)}/')

    if not args.move:
        print('\nRun with --move --yes to relocate these files automatically.')
        return 1

    for f, t in misplaced:
        src = os.path.join(ROOT, f)
        os.makedirs(t, exist_ok=True)
        dst = os.path.join(t, f)
        if os.path.exists(dst):
            print(f'SKIP move {f}: destination already exists: {dst}')
            continue
        if not args.yes:
            resp = input(f'Move {f} -> {dst}? [y/N]: ').strip().lower()
            if resp != 'y':
                print('skipped')
                continue
        shutil.move(src, dst)
        print(f'Moved {f} -> {dst}')

    print('Done.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
