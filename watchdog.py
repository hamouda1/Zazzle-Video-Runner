"""External scheduler entry point. Needs a repository-scoped Actions read/write token.

Run hourly outside GitHub. No Pinterest credentials and no public HTTP endpoint.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone, timedelta

REPO = 'hamouda1/Zazzle-Video-Runner'


def latest_slot(now):
    slot = now.replace(hour=now.hour // 4 * 4, minute=10, second=0, microsecond=0)
    return slot if slot <= now else slot - timedelta(hours=4)


def api(path, token, payload=None):
    request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Authorization':'Bearer ' + token, 'Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2022-11-28', 'Content-Type':'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        return json.loads(body) if body else None


def check(now, token, request=api):
    slot = latest_slot(now)
    if now - slot < timedelta(hours=1):
        return 'within_grace'
    # Bounded pagination; fail closed when a busy history cannot be resolved.
    for page in range(1, 6):
        runs = request('actions/workflows/run_video_publisher.yml/runs?per_page=100&page=' + str(page), token)['workflow_runs']
        for run in runs:
            created = datetime.fromisoformat(run['created_at'].replace('Z','+00:00'))
            if created >= slot and run['head_branch'] == 'main':
                if run['status'] != 'completed':
                    return 'already_active'
                if run.get('event') == 'schedule':
                    if run.get('conclusion') != 'success':
                        raise RuntimeError('Scheduled cycle failed; review required, no blind replay')
                    return 'scheduled_run_present'
                if run.get('display_title') == 'Recovery ' + slot.strftime('%Y-%m-%dT%H:%M:%SZ'):
                    if run.get('conclusion') != 'success':
                        raise RuntimeError('Recovery failed; review required')
                    return 'recovery_run_present'
                # A manual preview does not count as production. A previous
                # watchdog attempt is handled by the private per-slot ledger.
        if not runs or datetime.fromisoformat(runs[-1]['created_at'].replace('Z','+00:00')) < slot:
            break
    else:
        raise RuntimeError('Run history exceeds inspection limit')
    request('actions/workflows/run_video_publisher.yml/dispatches', token,
        {'ref':'main','inputs':{'dry_run':'false','upload_preview':'false',
                              'publication_slot':slot.strftime('%Y-%m-%dT%H:%M:%SZ')}})
    return 'dispatched_missing_slot'


if __name__ == '__main__':
    try:
        print(check(datetime.now(timezone.utc), os.environ['GH_TOKEN']))
    except Exception as error:
        print('Watchdog failed: ' + type(error).__name__ + '; no credentials logged')
        raise SystemExit(1)
