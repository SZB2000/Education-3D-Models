"""Publish a model as an immutable GitHub Release asset when either size limit is reached."""
import argparse,hashlib,http.client,json,subprocess,urllib.request,urllib.error,urllib.parse
from pathlib import Path
REPO='SZB2000/Education-3D-Models'
def publish(file,apk_bytes,force_remote=False,source_bytes=0):
    size=file.stat().st_size
    if not force_remote and max(size,source_bytes)<=100_000_000 and apk_bytes+size<=300_000_000:
        return {"delivery":"bundled","bytes":size}
    with file.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    account=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,check=True)
    token=dict(line.split('=',1) for line in account.stdout.splitlines() if '=' in line)['password']
    headers={'Authorization':'Bearer '+token,'User-Agent':'SuperLab-Model-Publisher','Content-Type':'application/json'}
    def api(path,data=None):
        req=urllib.request.Request('https://api.github.com/repos/'+REPO+path,headers=headers,data=None if data is None else json.dumps(data).encode())
        return json.load(urllib.request.urlopen(req,timeout=45))
    tag='models-v1'
    try:r=api('/releases/tags/'+tag)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        r=api('/releases',{'tag_name':tag,'name':'Education 3D Models','body':'On-demand models for Super Lab VR. Artist credits and original sources are in the repository README.'})
    name=file.stem+'-'+digest[:16]+file.suffix
    assets=[a for a in r['assets'] if a['name']==name]
    if assets:asset=assets[0]
    else:
        u=urllib.parse.urlsplit(r['upload_url'].split('{')[0])
        conn=http.client.HTTPSConnection(u.hostname,timeout=240)
        with file.open('rb') as f:conn.request('POST',u.path+'?'+urllib.parse.urlencode({'name':name}),body=f,headers={**headers,'Content-Type':'application/octet-stream','Content-Length':str(size)})
        resp=conn.getresponse();asset=json.load(resp);conn.close()
        if resp.status!=201:raise RuntimeError((resp.status,asset.get('message')))
    if asset['size']!=size or asset.get('digest') not in (None,'sha256:'+digest):raise ValueError("release verification failed")
    return {'delivery':'remote','url':asset['browser_download_url'],'bytes':size,'sha256':digest}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('--apk-bytes',type=int,required=True);p.add_argument('--source-bytes',type=int,default=0);p.add_argument('--remote',action='store_true');args=p.parse_args()
    print(json.dumps(publish(args.model,args.apk_bytes,args.remote,args.source_bytes),indent=2))
