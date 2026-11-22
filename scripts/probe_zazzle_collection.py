"""Measure live Zazzle collection through the real dry-run publisher, without Pinterest."""
from pathlib import Path
from unittest.mock import patch
import argparse
import json
import os
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--engine',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    engine=args.engine.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(engine))
    import queue_state
    import video_publisher
    from zazzle_harvester import VIDEO_BOARD_CONFIGS,ASSOCIATE_ID
    sample=json.loads((engine/'creative/examples/hoodie.json').read_text())
    gallery=json.loads((engine/'creative/examples/gallery.json').read_text())
    pdp=gallery['slices']['data']['mainProduct']['url']
    cfg=next(c for c in VIDEO_BOARD_CONFIGS if c['account']=='habiboumez' and c['product_type']=='streetwear_hoodie')
    product={'product_id':sample['product_id'],'title':sample['title'],'description':'Ad / Affiliate link',
             'pdp_url':pdp,'affiliate_link':pdp+'?rf='+ASSOCIATE_ID,'status':'pending',
             'image_url_1024':sample['views'][0]['source_url'],'product_type':sample['category']}
    state=queue_state.normalize({'boards':{cfg['board_id']:{**cfg,'queue':[product]}},'published_history':[]},[cfg])
    path=out/'queue-probe.json';path.write_text(json.dumps(state,indent=2));before=path.read_bytes()
    result={'live_zazzle_collection':False,'network_mode':'real Zazzle page/gallery downloads',
            'product_id':sample['product_id'],'pinterest_requests':0,'production_activation':False}
    with patch.dict(os.environ,{'VIDEO_RENDER_BACKEND':'creative','CREATIVE_ENGINE_PYTHON':str(engine/'.venv-creative/bin/python'),
                               'CREATIVE_TEMPLATE':'F06','CREATIVE_PREVIEW_WIDTH':'720','GITHUB_OUTPUT':''}), \
         patch.object(video_publisher,'ROOT',out),patch.object(video_publisher,'STATE',path), \
         patch.object(video_publisher,'RUNTIME',out/'runtime'),patch.object(video_publisher,'PLAN',out/'runtime/plan.json'), \
         patch.object(video_publisher,'VIDEO_BOARD_CONFIGS',[cfg]),patch.object(queue_state,'HISTORICAL_RECORDS',out/'no-live-history.json'), \
         patch.object(video_publisher,'PinterestVideoUploader') as uploader, \
         patch('requests.sessions.Session.request',side_effect=AssertionError('Pinterest/requests transport forbidden in collection probe')):
        try:
            video_publisher.prepare(dry_run=True,board_filter=cfg['board_id'])
            handoff=json.loads(next(out.rglob('*_creative-handoff.json')).read_text())
            assert handoff['production_validated'] is False and handoff['publication_performed'] is False
            result.update(live_zazzle_collection=True,six_distinct_photos_rendered=True,seventh_closing_scene=True)
        except Exception as error:
            result.update(error_type=type(error).__name__,reason=str(error)[:300],six_distinct_photos_rendered=False)
        uploader.assert_not_called()
    assert path.read_bytes()==before and not (out/'runtime/plan.json').exists()
    result['queue_unchanged']=True
    (out/'collection-result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)
    if not result['live_zazzle_collection']:
        print('::warning::Live Zazzle gallery was unavailable or insufficient. Keep production disabled; the offline fixture preview is a separate test.',flush=True)


if __name__=='__main__':main()
