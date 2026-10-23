"""Offline check: python scripts/check_roster_reference.py saved-source.html"""
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import unicodedata


def normalize(value):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower())


def check(source):
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root/'backend/app/data/players_2026.json').read_text(encoding='utf-8'))
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != data['source_sha256']:
        raise ValueError('Source snapshot checksum differs; review before updating.')
    club_ids = {normalize(club['name']):cid for cid,club in data['clubs'].items()}
    official = {}
    for heading,body in re.findall(r'<h5>(.*?)</h5>(.*?)(?=<h5>|$)', raw.decode('utf-8'), re.S):
        cid = club_ids[normalize(html.unescape(re.sub(r'<[^>]+>', '', heading)))]
        for row in re.split(r'<br\s*/?>|</p>', body):
            text = html.unescape(re.sub(r'<[^>]+>', '', row)).strip()
            match = re.fullmatch(r'(\d+)\s+([^\n]+)', text)
            if match:
                number,name = match.groups()
                official[normalize(name)] = (cid,int(number))
    if len(official) < 400:
        raise ValueError('Incomplete source article.')
    count = 0
    for cid,club in data['clubs'].items():
        for player in club['players']:
            if official.get(normalize(player['name'])) != (cid,player['number']):
                raise ValueError(f"Unconfirmed reference: {cid}/{player['id']}")
            count += 1
    print(f'{count} reference identities checked across {len(club_ids)} clubs; no network calls.')


if __name__ == '__main__':
    check(Path(sys.argv[1]))
