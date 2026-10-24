"""Check a judge URL using two new cookie sessions; never reads or prints Azure keys."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, urljoin
import uuid
import httpx


def check(url, local=False, recap=False, require_ai=False):
    parsed=urlsplit(url)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
        raise ValueError('Use the public root URL without credentials or query parameters')
    if parsed.scheme!='https' and not (local and parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost')):
        raise ValueError('Judging requires HTTPS; --local permits loopback HTTP tests only')
    report={'url':url,'scope':'local integration only' if local else 'HTTPS access from this machine; browser/phone checks still required', 'checks':{}}
    checks=report['checks']
    with httpx.Client(base_url=url,headers={'X-MatchOS-Client':'replay'},timeout=90,trust_env=False) as owner, httpx.Client(base_url=url,headers={'X-MatchOS-Client':'replay'},timeout=20,trust_env=False) as stranger:
        page=owner.get('/').raise_for_status()
        assert 'MatchOS' in page.text and 'id="root"' in page.text, 'Root page is not the built fan app'
        scripts=re.findall(r'<script[^>]+src="([^"]+)"',page.text)
        assert scripts and '@vite/client' not in page.text, 'Built JavaScript missing or a development server is exposed'
        for source in scripts:
            asset=urljoin(url,source)
            assert urlsplit(asset).netloc==parsed.netloc, 'Unexpected cross-origin script'
            assert urlsplit(asset).path.endswith('.js'), 'Development source is not a production bundle'
            owner.get(asset).raise_for_status()
        checks['built_fan_app']=True
        owner.get('/api/health').raise_for_status()
        checks['api_health']=True
        if not local:
            assert owner.get('/docs').status_code==404, 'Production API explorer is exposed'
            assert page.headers.get('strict-transport-security') and page.headers.get('content-security-policy'), 'Production security headers missing'
            checks['production_headers_and_hidden_docs']=True
        session=owner.post('/api/session',json={}).raise_for_status()
        cookie=session.headers.get('set-cookie','').lower()
        assert 'httponly' in cookie and 'samesite=strict' in cookie
        if not local:assert 'secure' in cookie
        checks['fresh_cookie_session']=True
        stranger.post('/api/session',json={}).raise_for_status()
        day='judge-check-'+uuid.uuid4().hex[:12]
        owner.post('/api/matchdays/start',json={'matchday_id':day}).raise_for_status()
        try:
            assert stranger.post(f'/api/matchdays/{day}/tick',json={'tick':1}).status_code==403, 'Another session can advance this replay'
            owner.post(f'/api/matchdays/{day}/tick',json={'tick':1}).raise_for_status()
            checks['replay_and_session_isolation']=True
            if recap or require_ai:
                for tick in range(2,33):owner.post(f'/api/matchdays/{day}/tick',json={'tick':tick}).raise_for_status()
                result=owner.post(f'/api/matches/{day}-featured/catch-up',json={}).raise_for_status().json()
                fan=result['fan_briefing']
                assert all(fan['spoken_recap'].get(language) for language in ('en','es'))
                report['recap_mode']=fan['narrative']['mode']
                report['recap_fallback_reason']=fan['narrative'].get('fallback_reason')
                if require_ai:assert report['recap_mode']=='azure', 'AI was not returned for this request'
                checks['bilingual_recap']=True
        finally:
            owner.request('DELETE',f'/api/matchdays/{day}',json={}).raise_for_status()
            checks['temporary_demo_released']=True
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    parser.add_argument('--local',action='store_true')
    parser.add_argument('--recap',action='store_true',help='One recap request; can consume private Azure capacity if configured')
    parser.add_argument('--require-ai',action='store_true',help='Additionally require an AI-authored recap, not fallback')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=check(args.url,args.local,args.recap,args.require_ai)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
