"""vol4のみEPUB再製本"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# build_all_epub.py のソースを読み、VOLUMES を差し替えて exec
src = open('C:/dev/build_all_epub.py', 'r', encoding='utf-8').read()

src = src.replace(
    'VOLUMES = [\n    {"dir": "vol1", "vol_num": 1, "subtitle": "第1巻"},\n    {"dir": "vol2", "vol_num": 2, "subtitle": "第2巻"},\n    {"dir": "vol3", "vol_num": 3, "subtitle": "第3巻"},\n    {"dir": "vol4", "vol_num": 4, "subtitle": "第4巻"},\n]',
    'VOLUMES = [{"dir": "vol4", "vol_num": 4, "subtitle": "第4巻"}]'
)
# stdout TextIOWrapper 二重化を回避
src = src.replace(
    'sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\'utf-8\')',
    '# stdout already wrapped by caller'
)
exec(compile(src, 'build_all_epub.py', 'exec'))
