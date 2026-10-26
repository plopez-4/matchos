import pytest
from app import matchday

@pytest.mark.parametrize('version', range(1, 5))
def test_explicit_test_version_is_stable_across_fixtures_and_private_ids(version):
    for suffix in ('abc123', 'phone-72ef', 'desktop-91cb'):
        for profile in matchday.PROFILES:
            assert matchday.selected_variant(f'test-v{version}-{suffix}-{profile["role"]}') == version - 1
