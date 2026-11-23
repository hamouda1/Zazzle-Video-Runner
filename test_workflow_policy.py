"""Read-only checks for the public Runner workflow; no private source or secrets."""
from pathlib import Path
import unittest
import yaml


class RunnerPolicy(unittest.TestCase):
    def setUp(self):
        self.text = Path('.github/workflows/run_video_publisher.yml').read_text()
        self.config = yaml.load(self.text, Loader=yaml.BaseLoader)
        self.steps = self.config['jobs']['execute-video-cycle']['steps']

    def test_existing_cadence_and_concurrency(self):
        self.assertEqual(self.config['on']['schedule'][0]['cron'], '10 */4 * * *')
        self.assertEqual(self.config['concurrency']['group'], 'zazzle-video-publisher')
        self.assertEqual(self.config['concurrency']['cancel-in-progress'], 'false')

    def test_preview_is_default_and_public_upload_requires_opt_in(self):
        inputs = self.config['on']['workflow_dispatch']['inputs']
        self.assertEqual(inputs['dry_run']['default'], 'true')
        self.assertEqual(inputs['upload_preview']['default'], 'false')
        upload = next(s for s in self.steps if s.get('uses', '').startswith('actions/upload-artifact'))
        self.assertIn('inputs.dry_run', upload['if'])
        self.assertIn('inputs.upload_preview', upload['if'])
        self.assertIn("github.event_name == 'workflow_dispatch'", upload['if'])
        self.assertNotIn('json', upload['with']['path'])
        self.assertNotIn('receipt', upload['with']['path'])

    def test_source_checkout_does_not_persist_git_credentials(self):
        checkout = next(s for s in self.steps if s.get('with', {}).get('repository') == 'hamouda1/Zazzle-Video-PinEngine')
        self.assertEqual(checkout['with']['persist-credentials'], 'false')
        self.assertEqual(checkout['with']['repository'], 'hamouda1/Zazzle-Video-PinEngine')

    def test_no_legacy_git_state_sync_or_error_suppression(self):
        for text in ('git push', 'git pull', 'git add', '|| true'):
            self.assertNotIn(text, self.text)

    def test_runtime_and_state_credentials_reach_only_publisher_step(self):
        publish = next(s for s in self.steps if s.get('name') == 'Execute Multi-Account Staggered Video Pin Publisher')
        self.assertIn('/.venv-creative/bin/python', publish['env']['CREATIVE_ENGINE_PYTHON'])
        self.assertIn('GH_PAT', publish['env'])
        self.assertIn('PINTEREST_ACCOUNTS_JSON', publish['env'])
        self.assertNotIn('env', self.config)


if __name__ == '__main__':
    unittest.main()
