from pathlib import Path
import sys,json,hashlib,subprocess,re,datetime
run=sys.argv[1];gpu=sys.argv[2]
t=Path('/mnt/public/xcj/Projects/state-vla/workspace/2a879870-8dda-4613-a684-0ad48a5e86be')
r=Path('/mnt/public/xcj/Projects/state-vla/RMBench/eval_result/memory_chunk_20260910')/run
d=t/'records'/run
rows=lambda name:[json.loads(x) for x in (r/name).read_text().splitlines() if x.strip()]
ep=rows('episode_diagnostics.jsonl');pre=rows('seed_preflight.jsonl');vid=rows('video_checks.jsonl');proc=rows('processes.jsonl')
checks={'exit0':(d/'exit').read_text().strip()=='0','exact100_fixed_seeds':len(ep)==100 and [(x['episode_id'],x['seed']) for x in ep]==[(i,100000+i) for i in range(100)],'accepted100':len(pre)==100 and all(x['accepted'] is True for x in pre) and [x['seed'] for x in pre]==list(range(100000,100100)),'terminal_without_error':all(x.get('error') in (None,'') and not x['diagnostics'].get('runtime_error') and x['diagnostics']['episode_status']['terminal'] for x in ep),'video_checks':len(vid)==100 and [(x['episode_id'],x['enabled'],x['ok']) for x in vid]==[(i,i<5,True) for i in range(100)],'no_video_files_after5':all(not (r/f'episode{i}.mp4').exists() for i in range(5,100)),'artifact_files':all((r/name).is_file() for name in ['command.txt','config.yaml','scheduler.yaml','episode0.json','episode1.json','diagnostics_summary.json','_result.txt'])}
video=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames,width,height','-of','json',str(r/'episode0.mp4')],text=True))
checks['decoded_video']=int(video['streams'][0]['nb_read_frames'])==vid[0]['frames']>0 and (r/'episode0.mp4').stat().st_size>0
checks['all_episode_artifacts']=all((r/f'episode{i}.json').is_file() for i in range(100))
for i in range(1,5):
 decoded=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=nb_read_frames','-of','json',str(r/f'episode{i}.mp4')],text=True))
 checks[f'decoded_video{i}']=int(decoded['streams'][0]['nb_read_frames'])==vid[i]['frames']>0
checks['score_in_64_74']=64<=sum(x['result']=='Success' for x in ep)<=74
starts={x['ordinal']:x for x in proc if x['event']=='start'};ends={x['ordinal']:x for x in proc if x['event']=='exit'}
checks['shutdown_records']=starts.keys()==ends.keys() and all((x['returncode']==0 if x['role']=='scheduler' else x['reason']=='runner_shutdown' and x['returncode'] in (0,-15)) for x in ends.values())
checks['services_gone']=all(not Path('/proc',str(x['pid'])).exists() for x in starts.values())
markers=['ErrorIncompatibleDriver','Your GPU driver does not support Vulkan','worker closed the RPC stream','ConnectionResetError','EOFError','Segmentation fault']
worker=(r/'processes/rmbench_sim_worker.stderr.log').read_text();errors={x:worker.count(x) for x in markers}
checks['worker_no_infra_errors']=not any(errors.values())
source={name:{'commit':subprocess.check_output(['git','-C',str(t/'formal/renderer-reviewed'/name),'rev-parse','HEAD'],text=True).strip(),'status':subprocess.check_output(['git','-C',str(t/'formal/renderer-reviewed'/name),'status','--porcelain','--untracked-files=no'],text=True)} for name in ['RMBench','robot-bridge','openpi']}
checks['clean_sources']=all(not x['status'] for x in source.values())
gpu_after=subprocess.check_output(['nvidia-smi','-i',gpu,'--query-gpu=index,uuid,memory.used','--format=csv,noheader'],text=True).strip();checks['gpu_reclaimed']=int(gpu_after.split(',')[-1].strip().split()[0])<100
receipt={'run':str(r),'verified_at':datetime.datetime.now().astimezone().isoformat(),'checks':checks,'passed':all(checks.values()),'episodes':[{'episode':x['episode_id'],'seed':x['seed'],'result':x['result'],'status':x['diagnostics']['episode_status']} for x in ep],'video':video,'gpu_after':gpu_after,'source':source,'infra_markers':errors,'sha256':{name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in ['seed_preflight.jsonl','episode_diagnostics.jsonl','video_checks.jsonl','_result.txt','episode0.mp4','processes.jsonl']}}
(d/'final-acceptance.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt));raise SystemExit(0 if receipt['passed'] else 1)
