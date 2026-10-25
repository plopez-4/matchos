"""Bounded speech-only hints; roster spellings and match facts remain unchanged."""
import json
import re
from importlib.resources import files
from xml.sax.saxutils import escape
from app.rosters import ROSTER_DATA

DATA = json.loads(files('app').joinpath('data/spanish_pronunciations.json').read_text(encoding='utf-8'))
CLUB_HINTS = {
    'manchester united': 'Mánchester Yunáited',
    'manchester city': 'Mánchester Siti',
    'crystal palace': 'Crístal Pálas',
    'newcastle united': 'Niucásel Yunáited',
    'palace': 'Pálas',
    'newcastle': 'Niucásel',
    'manchester': 'Mánchester',
    'united': 'Yunáited',
    'city': 'Siti',
}
HINTS = dict(CLUB_HINTS)
for entry in DATA['players']:
    for spelling in [entry['name'], *entry.get('variants', [])]:
        HINTS[spelling.casefold()] = entry['alias']
    for spelling, alias in entry.get('short_forms', {}).items():
        HINTS[spelling.casefold()] = alias
PATTERN = re.compile(r'\b(?:' + '|'.join(re.escape(name) for name in
                     sorted(HINTS, key=len, reverse=True)) + r')\b', re.IGNORECASE)
ROSTER_NAMES = tuple(dict.fromkeys(player['name'] for club in ROSTER_DATA['clubs'].values()
                                 for player in club['players']))
AUDITION_BATCH_SIZE = 12
TEAM_NAMES = {name for club in ROSTER_DATA['clubs'].values()
              for name in [club['name'], *club.get('aliases', [])]}
TEAM_NAMES.update(('United', 'City', 'Palace', 'Newcastle'))
TEAM_ALTERNATIVES = '|'.join(re.escape(name) for name in sorted(TEAM_NAMES, key=len, reverse=True))
TEAM_JOIN = re.compile(r'\b(?P<first>' + TEAM_ALTERNATIVES + r')\s+(?:y|e)\s+'
                       r'(?=(?:' + TEAM_ALTERNATIVES + r')\b)', re.IGNORECASE)

EN_CLOCK_PATTERN = re.compile(
    r'(?<!:\d{2}:)(?<!\d:)\b(?P<min>\d{1,3}):00(?!:\d{2})\b(?=(?P<already_min>\s+minutes?\b)?)'
)


def speech_markup(text, language):
    if language != 'es':
        if language == 'en':
            tokens = []
            for match in EN_CLOCK_PATTERN.finditer(text):
                minutes = int(match.group('min'))
                if match.group('already_min'):
                    alias = str(minutes)
                else:
                    alias = '1 minute' if minutes == 1 else f'{minutes} minutes'
                tokens.append((match.start(), match.end(),
                               f'<sub alias="{alias}">{escape(match.group(0))}</sub>'))
            if tokens:
                parts = []
                cursor = 0
                for start, end, markup in sorted(tokens, key=lambda token: token[0]):
                    parts.append(escape(text[cursor:start]))
                    parts.append(markup)
                    cursor = end
                parts.append(escape(text[cursor:]))
                return ''.join(parts)
        return escape(text)
    parts = []
    cursor = 0
    tokens = []
    for match in PATTERN.finditer(text):
        alias = escape(HINTS[match.group().casefold()], {'"': '&quot;'})
        tokens.append((match.start(), match.end(),
                       f'<sub alias="{alias}">{escape(match.group())}</sub>'))
    # A tiny phrasing boundary keeps consecutive foreign club names distinct.
    # The conjunction and every original character remain unchanged.
    for match in TEAM_JOIN.finditer(text):
        position = match.end('first')
        tokens.append((position, position, '<break time="120ms"/>'))
    for start, end, markup in sorted(tokens, key=lambda token: token[0]):
        parts.append(escape(text[cursor:start]))
        parts.append(markup)
        cursor = end
    parts.append(escape(text[cursor:]))
    return ''.join(parts)


def audition_names(batch):
    start = batch * AUDITION_BATCH_SIZE
    if batch < 0 or start >= len(ROSTER_NAMES):
        return ()
    return ROSTER_NAMES[start:start + AUDITION_BATCH_SIZE]
