"""Resolve slot from dispatch input or run creation, never delayed job start."""
import os
import urllib.request
import json
from datetime import datetime, timezone, timedelta
from watchdog import latest_slot

def resolve(raw, created, now):
    slot = datetime.strptime(raw, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc) if raw else latest_slot(created)
    if slot.hour % 4 or slot.minute != 10 or slot.second or slot > now or now-slot > timedelta(hours=8):
        raise ValueError('Invalid or stale slot; no backlog publication')
    return slot.strftime('%Y-%m-%dT%H:%M:%SZ')

if __name__ == '__main__':
    request = urllib.request.Request('https://api.github.com/repos/' + os.environ['GITHUB_REPOSITORY'] + '/actions/runs/' + os.environ['GITHUB_RUN_ID'], headers={'Authorization':'Bearer ' + os.environ['GH_TOKEN'], 'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        created = datetime.fromisoformat(json.load(response)['created_at'].replace('Z','+00:00'))
    slot = resolve(os.environ.get('REQUESTED_SLOT',''), created, datetime.now(timezone.utc))
    with open(os.environ['GITHUB_OUTPUT'],'a') as output:
        output.write('slot=' + slot + '\n')
