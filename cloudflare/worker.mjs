const base = 'https://api.github.com/repos/hamouda1/Zazzle-Video-Runner/';
export function latestSlot(now) {
  const slot = new Date(now);
  slot.setUTCHours(Math.floor(slot.getUTCHours()/4)*4,10,0,0);
  if(slot>now) slot.setUTCHours(slot.getUTCHours()-4);
  return slot;
}
export async function check(env, now = new Date(), request = fetch) {
  const slot=latestSlot(now), stamp=slot.toISOString().replace('.000','');
  if(now-slot<3600000) return {status:'grace',slot:stamp};
  const headers={'Accept':'application/vnd.github+json','User-Agent':'zazzle-publication-watchdog','X-GitHub-Api-Version':'2022-11-28'};
  if(env.GH_TOKEN) headers.Authorization='Bearer '+env.GH_TOKEN;
  for(let page=1;page<=5;page++) {
    const response=await request(base+'actions/workflows/run_video_publisher.yml/runs?per_page=30&page='+page,{headers,signal:AbortSignal.timeout(15000)});
    if(!response.ok) throw new Error('GitHub read HTTP '+response.status);
    const {workflow_runs:runs}=await response.json();
    if(!Array.isArray(runs)) throw new Error('Invalid run list');
    for(const run of runs) {
      if(new Date(run.created_at)<slot || run.head_branch!=='main') continue;
      if(run.status!=='completed') return {status:'active',slot:stamp};
      if(run.event==='schedule'||run.display_title==='Recovery '+stamp) {
        if(run.conclusion!=='success') throw new Error('Cycle failed; manual review required');
        return {status:'covered',slot:stamp};
      }
    }
    if(!runs.length||new Date(runs.at(-1).created_at)<slot) {
      if(!env.GH_TOKEN) return {status:'missing_slot_credentials_required',slot:stamp};
      const dispatched=await request(base+'actions/workflows/run_video_publisher.yml/dispatches',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({ref:'main',inputs:{dry_run:'false',upload_preview:'false',publication_slot:stamp}}),signal:AbortSignal.timeout(15000)});
      if(dispatched.status!==204) throw new Error('Dispatch HTTP '+dispatched.status);
      return {status:'dispatched',slot:stamp};
    }
  }
  throw new Error('Run history limit; no dispatch');
}
export default {
  async fetch() { return new Response('Not found',{status:404}); },
  async scheduled(event, env) {
    try { const result=await check(env,new Date(event.scheduledTime));console.log(JSON.stringify(result)); }
    catch(error) {console.error(JSON.stringify({status:'watchdog_failed',reason:error.message}));throw new Error('Watchdog check failed');}
  }
};
