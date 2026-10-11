"""Fail on likely credentials without printing their values (heuristic, not exhaustive)."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "provider token": re.compile(rb"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "key assignment": re.compile(rb'''(?i)(?:AZURE_OPENAI_API_KEY|api[_-]?key)["']?\s*[:=]\s*["']?([A-Za-z0-9_-]{32,})'''),
}


def check(data, location):
    failed = False
    for label, pattern in PATTERNS.items():
        for match in pattern.finditer(data):
            print(f"Possible {label}: {location}, line {data[:match.start()].count(bytes([10]))+1}")
            failed = True
    return failed


def main():
    failed = False
    paths = subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
    for raw in paths:
        if raw:
            path = ROOT / raw.decode()
            if path.is_file():
                failed |= check(path.read_bytes(), str(path.relative_to(ROOT)))
    for path in (ROOT/'frontend/dist').rglob('*'):
        if path.is_file():
            failed |= check(path.read_bytes(), str(path.relative_to(ROOT)))
    objects = subprocess.check_output(['git','rev-list','--objects','--all'],cwd=ROOT).splitlines()
    names = {item.partition(b' ')[0]:item.partition(b' ')[2].decode(errors='replace') for item in objects}
    data = subprocess.run(['git','cat-file','--batch'],input=b'\n'.join(names)+b'\n',capture_output=True,check=True,cwd=ROOT).stdout
    offset = 0
    while offset < len(data):
        end = data.index(b'\n',offset)
        oid, kind, size = data[offset:end].split()
        size = int(size)
        if kind == b'blob':
            failed |= check(data[end+1:end+1+size], 'Git '+oid.decode()[:12]+': '+names[oid])
        offset = end+1+size+1
    if not failed:
        print('No matching secret patterns in current files, built assets, or reachable local Git history.')
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
