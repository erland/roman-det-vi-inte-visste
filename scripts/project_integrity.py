#!/usr/bin/env python3
"""Romanprojekt: verifierbar SHA-256-baslinje och låsta revisionsändringar.
Kommandon: init, verify, status, commit. Revision 0 skapas endast från ny mall.
"""
import argparse,datetime,fnmatch,hashlib,json,re,sys,uuid
from pathlib import Path

M='project-manifest.json'; LOG='revision-log.md'; CH=re.compile(r'kapitel/kapitel-(\d{2,})\.md$')
def now():return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def sha(b):return hashlib.sha256(b).hexdigest()
def inv(root):
 return {str(p.relative_to(root)):{'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and p.name!=M and not set(p.relative_to(root).parts)&{'.git','.DS_Store','__MACOSX'}}
def chapters(files):
 nums=sorted(int(CH.fullmatch(k).group(1)) for k in files if CH.fullmatch(k));return {'count':len(nums),'first':nums[0] if nums else None,'latest':nums[-1] if nums else None,'missing':[n for n in range(nums[0],nums[-1]+1) if n not in nums] if nums else [],'hashes':{k:v['sha256'] for k,v in files.items() if CH.fullmatch(k)}}
def load(root):return json.loads((root/M).read_text(encoding='utf-8'))
def save(root,m):(root/M).write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def delta(a,b):return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
def verify(root,quiet=False):
 m=load(root); i=inv(root)
 assert isinstance(m['revision'],int) and m['revision']>=0,'Ogiltig revision'
 assert i==m['tracked_files'],'SHA-256 eller filinventering skiljer sig från manifestet: '+', '.join(delta(i,m['tracked_files']))
 assert chapters(i)==m['chapters'],'Kapitelinventering skiljer sig'
 assert re.search(r'-r\d{4}',m['canonical_zip_name']),'Kanoniskt zipnamn saknar revision'
 if not quiet:print(f"OK: revision {m['revision']} är verifierad. {len(i)} spårade filer, {m['chapters']['count']} kapitel, senaste kapitel {m['chapters']['latest']}.")
 return m

def log(root,rev,op,paths,name):
 p=root/LOG
 if not p.exists():p.write_text('# Revisionslogg\n\n| Revision | Tidpunkt (UTC) | Åtgärd | Ändrade filer | Zip-fil |\n|---:|---|---|---|---|\n',encoding='utf-8')
 with p.open('a',encoding='utf-8') as f:f.write(f"| {rev} | {now()} | {op.replace('|','/')} | {', '.join(paths)} | {name} |\n")
def init(args,root):
 f=root/M
 if f.exists():
  old=load(root)
  assert old.get('project_id','').startswith('TEMPLATE-'),'Init får inte skriva över modernt manifest'
 name=args.zip_name or f'{args.slug}-r{args.revision:04d}.zip'
 assert args.revision==0,'Nytt projekt ska börja med revision 0'
 log(root,0,args.operation,sorted(inv(root)),name);i=inv(root)
 m={'schema_version':1,'project_id':args.project_id or str(uuid.uuid4()),'project_slug':args.slug,'revision':0,'parent_revision':None,'created_at':now(),'updated_at':now(),'canonical_zip_name':name,'tracked_files':i,'chapters':chapters(i),'migration':None,'last_operation':{'type':'init','description':args.operation,'changed_files':sorted(i),'source_zip_name':None,'source_revision':None}}
 save(root,m);verify(root);print('Project ID:',m['project_id'])
def commit(args,root):
 m=verify(root,True) if False else load(root)
 assert m['revision']==args.expected_revision,'Fel källrevision'
 before=inv(root);changes=delta(m['tracked_files'],before)
 bad=[p for p in changes if not any(fnmatch.fnmatch(p,pattern) for pattern in args.allow)]
 assert not bad,'Otillåtna ändringar: '+', '.join(bad)
 assert not any(CH.fullmatch(p) and p not in args.allow and not any(fnmatch.fnmatch(p,pat) for pat in args.allow) for p in changes),'Ej tillåten kapiteländring'
 old=m['revision'];rev=old+1;log(root,rev,args.operation,changes,args.zip_name);i=inv(root)
 m.update(revision=rev,parent_revision=old,updated_at=now(),canonical_zip_name=args.zip_name,tracked_files=i,chapters=chapters(i),last_operation={'type':'commit','description':args.operation,'changed_files':sorted(set(changes+[LOG])),'source_zip_name':args.source_zip_name,'source_revision':old})
 save(root,m);verify(root)
def main():
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='cmd',required=True)
 q=sub.add_parser('init');q.add_argument('root');q.add_argument('--slug',required=True);q.add_argument('--revision',type=int,default=0);q.add_argument('--zip-name');q.add_argument('--project-id');q.add_argument('--operation',default='Skapade romanprojekt')
 q=sub.add_parser('verify');q.add_argument('root')
 q=sub.add_parser('status');q.add_argument('root')
 q=sub.add_parser('commit');q.add_argument('root');q.add_argument('--expected-revision',required=True,type=int);q.add_argument('--operation',required=True);q.add_argument('--zip-name',required=True);q.add_argument('--source-zip-name');q.add_argument('--allow',action='append',required=True)
 a=p.parse_args();root=Path(a.root).resolve()
 try:
  assert root.is_dir(),'Ingen projektkatalog'
  if a.cmd=='init':init(a,root)
  elif a.cmd=='verify':verify(root)
  elif a.cmd=='status':
   m=load(root);print(json.dumps({'project_id':m['project_id'],'revision':m['revision'],'chapters':chapters(inv(root)),'pending_changes':delta(m['tracked_files'],inv(root))},ensure_ascii=False,indent=2))
  elif a.cmd=='commit':commit(a,root)
 except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:print('FEL:',e,file=sys.stderr);return 1
 return 0
if __name__=='__main__':sys.exit(main())
