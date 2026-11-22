"""Validate the pinned engine, credential boundaries and publication checkpoint order."""
from pathlib import Path
import argparse
import json
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]


def validate(workflow,contract):
    def require(value,message):
        if not value:raise ValueError(message)
    require(re.fullmatch('[0-9a-f]{40}',contract['engine_code_sha']),'Engine must use an exact commit')
    env=workflow['env'];job=workflow['jobs']['execute-video-cycle'];steps=job['steps']
    require(env['ENGINE_CODE_SHA']==contract['engine_code_sha'],'Workflow/contract engine pin mismatch')
    require(env.get('VIDEO_RENDER_BACKEND')=='creative','Creative backend not selected')
    require('.venv-creative/bin/python' in env.get('CREATIVE_ENGINE_PYTHON',''),'Isolated creative interpreter missing')
    require('secrets.' not in json.dumps(env),'Credentials must not be in global workflow environment')
    require(workflow['on']['workflow_dispatch']['inputs']['dry_run']['default']=='true','Manual mode must default to preview')
    require(workflow['on']['workflow_dispatch']['inputs']['upload_preview']['default']=='false','Public artifacts require explicit opt-in')
    require(workflow['concurrency']['cancel-in-progress']=='false','Publication must not be cancelled mid-attempt')
    require(job['runs-on']==contract['runner'],'Unexpected runner platform')
    require('refs/heads/main' in job['if'] and 'VIDEO_PUBLISH_ENABLED' in job['if'] and 'CREATIVE_IMAGE_RIGHTS_CONFIRMED' in job['if'],'Schedule opt-in gates missing')
    require(workflow['permissions']=={'contents':'read'},'Workflow permissions must remain read-only')
    names=[s.get('name','') for s in steps]
    expected=['Check explicit live publication policy','Checkout tested private engine code',
              'Install isolated locked creative renderer','Verify publisher contract and offline tests',
              'Load latest queue state independently of pinned code','Prepare media and local publication reservation',
              'Durably checkpoint queue before any Pin creation','Create exactly one reserved Pin attempt',
              'Persist result or review-required marker']
    require(all(name in names for name in expected),'Required checkpoint/install stage missing')
    require([names.index(n) for n in expected]==sorted(names.index(n) for n in expected),'Publication/checkpoint order changed')
    checkout=steps[names.index('Checkout tested private engine code')]
    require(checkout['with']['repository']==contract['engine_repository'],'Wrong engine repository')
    require(checkout['with']['ref']=='${{ env.ENGINE_CODE_SHA }}','Checkout must use tested engine pin')
    require(checkout['with']['persist-credentials']=='false','Checkout must not persist state credentials')
    require(any(s.get('with',{}).get('python-version')==contract['python'] for s in steps),'Python 3.12 required')
    allowed_pin_steps={'Prepare media and local publication reservation','Create exactly one reserved Pin attempt'}
    allowed_state_steps={'Load latest queue state independently of pinned code','Durably checkpoint queue before any Pin creation','Persist result or review-required marker'}
    for step in steps:
        name=step.get('name','');scoped=step.get('env',{})
        require(step.get('continue-on-error')!='true','Failures must not be ignored')
        require('|| true' not in step.get('run',''),'State writes must not suppress errors')
        if 'PINTEREST_ACCOUNTS_JSON' in scoped:require(name in allowed_pin_steps,'Pinterest token leaked to unrelated stage')
        if 'ENGINE_STATE_TOKEN' in scoped:require(name in allowed_state_steps,'State credential leaked to unrelated stage')
    checkpoint=steps[names.index('Durably checkpoint queue before any Pin creation')]
    publish=steps[names.index('Create exactly one reserved Pin attempt')]
    require(checkpoint.get('id')=='checkpoint' and "steps.checkpoint.outcome == 'success'" in publish['if'],'Pin creation requires durable checkpoint success')
    artifact=steps[names.index('Upload explicitly requested public preview')]
    require('inputs.upload_preview' in artifact['if'] and 'inputs.dry_run' in artifact['if'],'Public artifact upload is not explicitly gated')
    return contract['engine_code_sha']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args()
    workflow=yaml.load((ROOT/'.github/workflows/run_video_publisher.yml').read_text(),Loader=yaml.BaseLoader)
    contract=json.loads((ROOT/'workflow-contract.json').read_text())
    sha=validate(workflow,contract)
    if args.output:
        with open(args.output,'a',encoding='utf-8') as stream:stream.write('engine_sha='+sha+'\n')
    print('Runner workflow contract verified; pinned engine '+sha)


if __name__=='__main__':main()
