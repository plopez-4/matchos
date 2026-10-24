"""Dashboard adapter for the same authored fixtures used by the fan experience."""
from app.matchday import PROFILES, DURATION, VERSION, DEMO_FIXTURES, VARIANTS, fixture, library_fixture
from app.rosters import club_for_name

FULL_MATCHES = {item['id']: item for item in DEMO_FIXTURES}


def generate_full_match(scenario_id, seed=7, match_id='full-match', variant=None):
    config = FULL_MATCHES[scenario_id]
    profile = next(item for item in PROFILES if item['role'] == config['role'])
    return (library_fixture(profile, match_id, variant) if variant is not None
            else fixture(profile, match_id, seed=seed))


def full_match_catalog():
    return [dict(id=sid, name=config['name'], description=config['description'],
                 event_count=len(generate_full_match(sid)), duration_seconds=DURATION,
                 scenario_version=VERSION, data_origin='synthetic',
                 version_count=len(VARIANTS[config['role']]),
                 teams={side: {'name': config[side], 'players': club_for_name(config[side])['players']}
                        for side in ('home', 'away')})
            for sid, config in FULL_MATCHES.items()]
