import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
import watchdog
from prepare_slot import resolve

class WatchdogTests(unittest.TestCase):
    def test_delayed_job_uses_creation_slot(self):
        created=datetime(2026,11,23,4,12,tzinfo=timezone.utc)
        now=datetime(2026,11,23,8,30,tzinfo=timezone.utc)
        self.assertEqual(resolve('',created,now),'2026-11-23T04:10:00Z')
    def test_future_and_stale_slots_rejected(self):
        now=datetime(2026,11,23,16,30,tzinfo=timezone.utc)
        for value in ['2026-11-23T20:10:00Z','2026-11-23T04:10:00Z','2026-11-23T12:10:01Z']:
            with self.assertRaises(ValueError): resolve(value,now,now)
    def test_active_run_prevents_dispatch(self):
        api=Mock(return_value={'workflow_runs':[{'created_at':'2026-11-23T04:11:00Z','head_branch':'main','status':'in_progress'}]})
        self.assertEqual(watchdog.check(datetime(2026,11,23,6,tzinfo=timezone.utc),'fake',api),'already_active')
        self.assertEqual(api.call_count,1)
    def test_grace_does_not_call_api(self):
        api=Mock(); self.assertEqual(watchdog.check(datetime(2026,11,23,4,30,tzinfo=timezone.utc),'fake',api),'within_grace'); api.assert_not_called()
    def test_missing_slot_dispatches_explicit_live_slot(self):
        api=Mock(return_value={'workflow_runs':[]})
        self.assertEqual(watchdog.check(datetime(2026,11,23,6,tzinfo=timezone.utc),'fake',api),'dispatched_missing_slot')
        self.assertEqual(api.call_args.args[2]['inputs']['publication_slot'],'2026-11-23T04:10:00Z')
    def test_failed_schedule_not_blindly_replayed(self):
        api=Mock(return_value={'workflow_runs':[{'created_at':'2026-11-23T04:11:00Z','head_branch':'main','status':'completed','event':'schedule','conclusion':'failure'}]})
        with self.assertRaises(RuntimeError): watchdog.check(datetime(2026,11,23,6,tzinfo=timezone.utc),'fake',api)
        self.assertEqual(api.call_count,1)

if __name__ == '__main__': unittest.main()
