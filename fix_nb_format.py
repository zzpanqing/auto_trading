"""
Convert all Jupyter notebook cell sources from single-string to
array-of-strings format, so git diffs show per-line changes.

Usage:
    python fix_nb_format.py [notebook.ipynb]

If no argument is given, defaults to trading_bot_colab_multi.ipynb.
"""

import json
import pathlib
import sys


def fix(path: pathlib.Path) -> None:
    nb = json.loads(path.read_text(encoding='utf-8'))
    changed = 0
    for cell in nb['cells']:
        src = cell.get('source', '')
        if isinstance(src, str):
            lines = src.split('\n')
            cell['source'] = (
                [line + '\n' for line in lines[:-1]]
                + ([lines[-1]] if lines[-1] != '' else [])
            )
            changed += 1
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'Fixed {changed} cell(s) in {path}')


if __name__ == '__main__':
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path('trading_bot_colab_multi.ipynb')
    fix(target)
