from pathlib import Path
import copy
import importlib.util
import json
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'scripts/validate_workflow.py');validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow=yaml.load((ROOT/'.github/workflows/run_video_publisher.yml').read_text(),Loader=yaml.BaseLoader)
        self.contract=json.loads((ROOT/'workflow-contract.json').read_text())

    def invalid(self,change):
        value=copy.deepcopy(self.workflow);change(value)
        with self.assertRaises(ValueError):validator.validate(value,self.contract)

    def test_workflow_matches_reviewed_contract(self):
        self.assertEqual(validator.validate(self.workflow,self.contract),self.contract['engine_code_sha'])

    def test_wrong_or_floating_engine_pin_rejected(self):
        self.invalid(lambda w:w['env'].update(ENGINE_CODE_SHA='main'))

    def test_manual_live_default_rejected(self):
        self.invalid(lambda w:w['on']['workflow_dispatch']['inputs']['dry_run'].update(default='false'))

    def test_public_artifact_default_rejected(self):
        self.invalid(lambda w:w['on']['workflow_dispatch']['inputs']['upload_preview'].update(default='true'))

    def test_global_token_leak_rejected(self):
        self.invalid(lambda w:w['env'].update(PINTEREST_ACCOUNTS_JSON='${{ secrets.PINTEREST_ACCOUNTS_JSON }}'))

    def test_missing_checkpoint_rejected(self):
        self.invalid(lambda w:w['jobs']['execute-video-cycle']['steps'].__setitem__(slice(None),[s for s in w['jobs']['execute-video-cycle']['steps'] if s.get('id')!='checkpoint']))

    def test_unguarded_pin_attempt_rejected(self):
        def change(w):
            next(s for s in w['jobs']['execute-video-cycle']['steps'] if s.get('name')=='Create exactly one reserved Pin attempt')['if']='${{ success() }}'
        self.invalid(change)

    def test_persisted_checkout_credentials_rejected(self):
        def change(w):
            next(s for s in w['jobs']['execute-video-cycle']['steps'] if s.get('name')=='Checkout tested private engine code')['with']['persist-credentials']='true'
        self.invalid(change)

    def test_missing_schedule_gate_rejected(self):
        self.invalid(lambda w:w['jobs']['execute-video-cycle'].update({'if':"github.ref == 'refs/heads/main'"}))


if __name__=='__main__':unittest.main()
