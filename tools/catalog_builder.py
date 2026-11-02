import os,sys,json,pathlib,urllib.request,urllib.parse,urllib.error,subprocess,hashlib,tempfile,re,math,time
R='SZB2000/Education-3D-Models'
API='https://api.github.com/repos/'+R
T={'low':(15000,1024),'medium':(40000,2048),'high':(75000,4096)}
def request(url,data=None,method=None):
 headers={'User-Agent':'SuperLab-Model-Builder','Authorization':'Bearer '+os.environ['GH_TOKEN']}
 if data is not None:headers['Content-Type']='application/json'
 req=urllib.request.Request(url,headers=headers,data=None if data is None else json.dumps(data).encode(),method=method)
 return json.load(urllib.request.urlopen(req,timeout=60))
def triangles(file):
 with open(file,'rb') as f:
  h=f.read(20);doc=json.loads(f.read(int.from_bytes(h[12:16],'little')))
 counts=[sum(doc['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']//3 for p in m['primitives'] if p.get('mode',4)==4) for m in doc.get('meshes',[])]
 return sum(counts[n['mesh']] for n in doc['nodes'] if 'mesh' in n)
def convert(src,name,tiers,out):
 src=pathlib.Path(src); out=pathlib.Path(out);out.mkdir(exist_ok=True)
 records=[]
 with tempfile.TemporaryDirectory() as tmp:
  for tier in tiers:
   cap,px=T[tier];base=pathlib.Path(tmp)/'base.glb'
   subprocess.run([os.getenv('BLENDER','blender'),'-b','--factory-startup','--disable-autoexec','--python-exit-code','1','--python',str(pathlib.Path(__file__).with_name('convert_blender.py')),'--',str(src.resolve()),str(base),str(px)],check=True,timeout=600)
   count=triangles(base);target=out/(tier+'.glb')
   if not count:raise ValueError('No triangles')
   for attempt in range(3):
    ratio=min(1.,cap/count*(.98,.82,.55)[attempt])
    subprocess.run([os.getenv('GLTFPACK','gltfpack'),'-i',str(base),'-o',str(target),'-noq','-kn','-km','-ac','-af','0','-si',str(ratio),'-sa'],check=True,timeout=300)
    actual=triangles(target)
    if 0<actual<=cap:break
   else:raise ValueError('Cannot meet requested triangle budget')
   digest=hashlib.sha256(target.read_bytes()).hexdigest()
   records.append(dict(id=hashlib.sha256((name.casefold()+':'+tier).encode()).hexdigest()[:20],name=name[:64],tier=tier,sha256=digest,triangles=actual,bytes=target.stat().st_size))
 (out/'records.json').write_text(json.dumps(records),encoding='utf8')
if __name__=='__main__':
 import base64
 mode=sys.argv[1];out=pathlib.Path('converted')
 if mode=='convert':
  # Only files in the checked-out workspace or the uploader's release are accepted.
  if os.environ.get('SOURCE_ID'):
   asset=request(API+'/releases/assets/'+str(int(os.environ['SOURCE_ID'])))
   assert re.fullmatch(r'src-[0-9a-f]{32}\.(glb|gltf|fbx|obj|ply|stl|dae)',asset['name']) and asset['size']<=200*1024**2
   src=pathlib.Path(asset['name'])
   import shutil
   with urllib.request.urlopen(asset['browser_download_url'],timeout=120) as r,src.open('wb') as f:shutil.copyfileobj(r,f)
   convert(src,os.environ['MODEL_NAME'],os.environ['TIERS'].split(','),out)
  else:
   raw=subprocess.check_output(['git','diff','--name-only','--diff-filter=AM','-z',os.environ['BEFORE'],'HEAD'])
   paths=[pathlib.Path(os.fsdecode(x)) for x in raw.split(b'\0') if x]
   paths=[p for p in paths if p.suffix.lower() in ('.glb','.gltf','.obj','.stl','.ply','.fbx','.dae')]
   for i,p in enumerate(paths):
    dest=out/str(i);dest.mkdir(parents=True,exist_ok=True);convert(p,p.stem,list(T),dest)
 else:
  records=[]
  release=request(API+'/releases/tags/models-v1')
  for f in out.rglob('records.json'):
   for rec in json.loads(f.read_text()):
    key=rec['sha256']+'.glb';target=f.parent/(rec['tier']+'.glb')
    assert hashlib.sha256(target.read_bytes()).hexdigest()==rec['sha256']
    url='https://github.com/'+R+'/releases/download/models-v1/'+key
    try:
     import http.client
     conn=http.client.HTTPSConnection('uploads.github.com',timeout=180)
     with target.open('rb') as h:conn.request('POST','/repos/'+R+'/releases/'+str(release['id'])+'/assets?name='+key,body=h,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'User-Agent':'SuperLab','Content-Type':'application/octet-stream','Content-Length':str(target.stat().st_size)})
     response=conn.getresponse();msg=json.load(response)
     if response.status!=201 and not(response.status==422 and any(e.get('code')=='already_exists' for e in msg.get('errors',[]))):raise ValueError(str(msg))
    finally:conn.close()
    records.append(dict(rec,url=url))
  if records:
   current=request(API+'/contents/catalog.json')
   data=json.loads(base64.b64decode(current['content']));byid={r['id']:r for r in data['models']};byid.update({r['id']:r for r in records});data['models']=list(byid.values());data['updated']=int(time.time())
   request(API+'/contents/catalog.json',{'message':'Update downloadable classroom models','sha':current['sha'],'content':base64.b64encode((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()).decode()},'PUT')
