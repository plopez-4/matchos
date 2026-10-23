"""Inventory every bundled identity and optionally generate bounded EN/ES auditions.

Uses the running development server's private Speech configuration, never keys.
Audio generation is not listening or native-speaker pronunciation approval.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from app.pronunciation import DATA, ROSTER_NAMES, AUDITION_BATCH_SIZE, audition_names
from app.rosters import ROSTER_DATA
from app.narration import build_ssml, PROFILES
import httpx


def write_report(folder, report):
    (folder / 'audit.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    rows = []
    for batch in report['batches']:
        clips = []
        for profile, clip in batch['clips'].items():
            if clip['status'] == 'generated':
                clips.append(f'<p>{html.escape(profile)}: <audio controls preload="none" '
                             f'src="{clip["file"]}"></audio></p>')
        names = '<br>'.join(html.escape(name) for name in batch['names'])
        rows.append(f'<section><h2>Group {batch["batch"] + 1}</h2><p>{names}</p>'
                    + ''.join(clips) + '</section>')
    locale = 'Spanish' if report['language'] == 'es' else 'English'
    page = ('<!doctype html><html lang="en"><meta charset="utf-8">'
            f'<title>MatchOS {locale} player-name auditions</title>'
            '<style>body{font:18px system-ui;max-width:900px;margin:40px auto;padding:20px;'
            'background:#160520;color:#fff}section{border-top:1px solid #78617f;padding:20px 0}'
            'audio{display:block;width:100%;margin:10px 0}a{color:#80ffba}</style>'
            f'<h1>{locale} player-name auditions</h1><p>All {report["player_count"]} bundled player names, in roster order. '
            'Each group has both the Matchday and Warm voice. '
            'Audio generation has been checked; pronunciation has not been signed off by a listener.</p>'
            '<p>Some names have pronunciation hints adapted from official guides. '
            'Others use the voice’s default pronunciation. Match text and identity spellings are unchanged.</p>'
            + ''.join(rows) + '</html>')
    (folder / 'index.html').write_text(page, encoding='utf-8')


def audit_language(language, live):
    locale = 'spanish' if language == 'es' else 'english'
    folder = ROOT / 'docs' / f'{locale}-player-name-audit'
    folder.mkdir(parents=True, exist_ok=True)
    previous = json.loads((folder / 'audit.json').read_text(encoding='utf-8')) if (folder / 'audit.json').exists() else {}
    hints = {entry['name']: entry for entry in DATA['players']} if language == 'es' else {}
    report = {'language': language, 'lexicon_version': DATA['version'] if language == 'es' else 'provider-default-en-v1',
              'player_count': len(ROSTER_NAMES),
              'hinted_players': len(hints), 'listening_approved_players': 0,
              'note': DATA['note'] if language == 'es' else 'Default English provider pronunciation; no listening sign-off.',
              'sources': DATA['sources'], 'players': [], 'batches': []}
    for club_id, club in ROSTER_DATA['clubs'].items():
        for player in club['players']:
            hint = hints.get(player['name'])
            report['players'].append({'name': player['name'], 'club': club_id,
                                      f'alias_{language}': hint['alias'] if hint else None,
                                      'hint_basis': hint.get('basis', 'written_reference') if hint else None,
                                      'source': DATA['sources'][hint['source']] if hint else None,
                                      'listening_status': 'pending'})
    for batch in range((len(ROSTER_NAMES) + AUDITION_BATCH_SIZE - 1) // AUDITION_BATCH_SIZE):
        names = audition_names(batch)
        clips = {}
        old = next((entry for entry in previous.get('batches', []) if entry['batch'] == batch), {})
        for profile in ('matchday', 'warm'):
            clip = old.get('clips', {}).get(profile)
            filename = f'group-{batch + 1:02d}-{profile}.mp3'
            ssml, _, _ = build_ssml({'audience': 'advanced',
                                     'spoken_recap': {language: '. '.join(names) + '.'}}, language, profile)
            fingerprint = hashlib.sha256(ssml.encode()).hexdigest()
            if (clip and clip.get('ssml_sha256') == fingerprint and (folder / filename).exists()
                    and hashlib.sha256((folder / filename).read_bytes()).hexdigest() == clip['sha256']):
                clips[profile] = clip
        report['batches'].append({'batch': batch, 'names': names, 'clips': clips})
    write_report(folder, report)
    if not live:
        print(f'Inventoried {len(ROSTER_NAMES)} names; {len(hints)} targeted hints. No Azure calls.')
        return
    with httpx.Client(base_url='http://127.0.0.1:8000', timeout=25,
                      headers={'X-MatchOS-Client': 'replay'}, trust_env=False) as client:
        client.post('/api/session', json={}).raise_for_status()
        status = client.get('/api/narration/status').raise_for_status().json()
        if not status['available']:
            raise SystemExit('Azure Speech is not configured. No audio requested.')
        next_request = time.monotonic()
        for batch in report['batches']:
            for profile in ('matchday', 'warm'):
                if profile in batch['clips']:
                    print(f'Group {batch["batch"] + 1} {profile}: unchanged clip retained', flush=True)
                    continue
                time.sleep(max(0, next_request - time.monotonic()))
                next_request = time.monotonic() + 10.5  # At most six requests per minute.
                response = client.post('/api/narration/audition', json={
                    'language': language, 'voice_profile': profile, 'roster_batch': batch['batch']})
                response.raise_for_status()
                audio = response.content
                if not response.headers.get('content-type', '').startswith('audio/mpeg') or not audio:
                    raise SystemExit('No playable MP3 returned; stopping audit.')
                if response.headers.get('x-matchos-voice') != PROFILES[profile][language][0]:
                    raise SystemExit('Unexpected voice returned; stopping audit.')
                filename = f'group-{batch["batch"] + 1:02d}-{profile}.mp3'
                (folder / filename).write_bytes(audio)
                batch['clips'][profile] = {'status': 'generated', 'file': filename,
                    'bytes': len(audio), 'sha256': hashlib.sha256(audio).hexdigest(),
                    'ssml_sha256': hashlib.sha256(build_ssml({'audience': 'advanced',
                        'spoken_recap': {language: '. '.join(batch['names']) + '.'}}, language, profile)[0].encode()).hexdigest(),
                    'voice': response.headers.get('x-matchos-voice')}
                write_report(folder, report)
                print(f'Group {batch["batch"] + 1}/{len(report["batches"])} {profile}: '
                      f'{len(batch["names"])} names, {len(audio)} bytes', flush=True)
    print('All clips generated. Listening approval remains pending.', flush=True)


def combined_report():
    folder = ROOT / 'docs' / 'bilingual-player-name-audit'
    folder.mkdir(parents=True, exist_ok=True)
    reports = {}
    for language, locale in (('en', 'english'), ('es', 'spanish')):
        source = ROOT / 'docs' / f'{locale}-player-name-audit' / 'audit.json'
        if source.exists():
            reports[language] = json.loads(source.read_text(encoding='utf-8'))
    sections = []
    for index in range((len(ROSTER_NAMES) + AUDITION_BATCH_SIZE - 1) // AUDITION_BATCH_SIZE):
        names = '<br>'.join(html.escape(name) for name in audition_names(index))
        players = []
        for language, report in reports.items():
            locale = 'English' if language == 'en' else 'Spanish'
            batch = next(entry for entry in report['batches'] if entry['batch'] == index)
            for profile, clip in batch['clips'].items():
                players.append(f'<p>{locale} · {html.escape(profile)} · {html.escape(clip["voice"])}'
                               f'<audio controls preload="none" src="../{locale.lower()}-player-name-audit/{clip["file"]}"></audio></p>')
        sections.append(f'<section><h2>Group {index + 1}</h2><p>{names}</p>' + ''.join(players) + '</section>')
    (folder / 'audit.json').write_text(json.dumps({'player_count': len(ROSTER_NAMES),
        'listening_approved_players': 0, 'languages': reports}, ensure_ascii=False, indent=2), encoding='utf-8')
    (folder / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<title>MatchOS bilingual player-name review</title><style>body{font:18px system-ui;'
        'max-width:900px;margin:30px auto;padding:20px;background:#160520;color:white}'
        'section{border-top:1px solid #78617f;padding:20px 0}audio{display:block;width:100%;margin:8px 0}</style>'
        '<h1>English and Spanish player-name review</h1>'
        f'<p>{len(ROSTER_NAMES)} names · four voice profiles. Playback samples are not pronunciation approval.</p>'
        '<p>Listening approval remains pending for every name. English uses default provider pronunciation; '
        f'Spanish uses targeted hints for {reports.get("es", {}).get("hinted_players", 0)} names. '
        'Compare each name across the four voices below.</p>'
        + ''.join(sections) + '</html>', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Generate missing clips using configured Azure Speech')
    parser.add_argument('--language', choices=('en', 'es', 'both'), default='es')
    args = parser.parse_args()
    for language in (('en', 'es') if args.language == 'both' else (args.language,)):
        audit_language(language, args.live)
    combined_report()


if __name__ == '__main__':
    main()
