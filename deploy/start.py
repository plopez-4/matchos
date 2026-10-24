"""Single-worker container entry point. Secrets are read only by the application."""
import os
import sys


def main():
    if os.getenv('MATCHOS_ENV','local')=='production':
        for name in ('MATCHOS_ALLOWED_HOSTS','MATCHOS_ALLOWED_ORIGINS'):
            if not os.getenv(name):
                raise SystemExit(name+' must be configured for the public hostname')
    # Container Apps HTTP ingress owns forwarded headers. Uvicorn must not trust
    # arbitrary proxy chains; the explicit platform adapter handles that boundary.
    os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app',
        '--app-dir','backend','--host','0.0.0.0','--port','8000','--workers','1','--no-proxy-headers'])


if __name__=='__main__':main()
