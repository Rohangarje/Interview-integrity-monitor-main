#!/usr/bin/env python3
"""Find and optionally delete duplicate files by content hash.

Usage:
  python scripts/remove_duplicates.py --path . [--dry-run] [--delete]

Defaults to safe dry-run mode. The script ignores common virtualenv and VCS folders.
"""
import argparse
import hashlib
import os
import sys


IGNORE_DIRS = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules'}
IGNORE_FILES = {'db.sqlite3'}


def file_hash(path, block_size=65536):
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                h.update(block)
    except Exception:
        return None
    return h.hexdigest()


def find_duplicates(root):
    sizes = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # modify dirnames in-place to skip ignored dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            if fn in IGNORE_FILES:
                continue
            full = os.path.join(dirpath, fn)
            if not os.path.isfile(full):
                continue
            try:
                sz = os.path.getsize(full)
            except OSError:
                continue
            sizes.setdefault(sz, []).append(full)

    # For files with same size, compute hash
    groups = {}
    for sz, paths in sizes.items():
        if len(paths) < 2:
            continue
        for p in paths:
            h = file_hash(p)
            if h is None:
                continue
            groups.setdefault(h, []).append(p)

    # only return groups with duplicates
    return [g for g in groups.values() if len(g) > 1]


def main():
    parser = argparse.ArgumentParser(description='Detect and optionally delete duplicate files')
    parser.add_argument('--path', '-p', default='.', help='Root path to scan')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Only list duplicates (default)')
    parser.add_argument('--delete', action='store_true', help='Delete duplicate files (keep one copy)')
    args = parser.parse_args()

    # If user passed --delete, we disable dry-run
    if args.delete:
        args.dry_run = False

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print('Path is not a directory:', root, file=sys.stderr)
        sys.exit(1)

    print('Scanning:', root)
    dup_groups = find_duplicates(root)
    if not dup_groups:
        print('No duplicate files found.')
        return

    print(f'Found {len(dup_groups)} duplicate groups:\n')
    total_candidates = 0
    for i, group in enumerate(dup_groups, 1):
        print(f'Group {i}:')
        for p in group:
            print('  ', p)
        total_candidates += len(group) - 1
        print()

    print(f'Total duplicate files that can be removed (keeping one per group): {total_candidates}')

    if args.dry_run:
        print('\nDry-run mode: no files were deleted. To delete, re-run with --delete')
        return

    # Deletion path
    removed = 0
    for group in dup_groups:
        # keep the first path (sorted for determinism)
        keep = sorted(group)[0]
        for p in group:
            if p == keep:
                continue
            try:
                os.remove(p)
                print('Removed', p)
                removed += 1
            except Exception as e:
                print('Failed to remove', p, '-', e)

    print(f'Deleted {removed} files.')


if __name__ == '__main__':
    main()
