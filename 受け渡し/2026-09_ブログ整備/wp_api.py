import os,sys,json,base64,urllib.request,urllib.error,pathlib
BASE='https://sekkotsuin-komaki.com'
ROOT=pathlib.Path(__file__).resolve().parent
def api(path,data=None,method=None,extra=None):
    headers={'Authorization':'Basic '+base64.b64encode(('btgkmksys:'+os.environ['WP_APP_PASSWORD']).encode()).decode(),'User-Agent':'BTG editorial update'}
    if data is not None and not isinstance(data,bytes):
        data=json.dumps(data,ensure_ascii=False).encode();headers['Content-Type']='application/json'
    headers.update(extra or {})
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as res:return json.load(res)
    except urllib.error.HTTPError as e:
        print('HTTP error',e.code,'for',path.split('?')[0]);sys.exit(1)
def save(name,data):
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
    action=sys.argv[1]
    if action=='refresh':
        posts=api('/wp-json/wp/v2/posts?status=draft,future&context=edit&per_page=100');save('wp-latest.json',posts)
        cats=api('/wp-json/wp/v2/categories?per_page=100');save('wp-categories.json',cats)
        settings=api('/wp-json/wp/v2/settings');save('wp-settings.json',settings)
        print(json.dumps({'posts':[{'id':p['id'],'title':p['title']['raw'],'modified':p['modified'],'status':p['status'],'length':len(p['content']['raw'])}for p in posts],'categories':[{'id':c['id'],'name':c['name']}for c in cats],'timezone':settings.get('timezone')},ensure_ascii=False))
    elif action=='media':
        ids=sys.argv[2]
        media=api('/wp-json/wp/v2/media?include='+ids+'&per_page=100');save('existing-media.json',media)
        print(json.dumps([{'id':m['id'],'url':m['source_url'],'alt':m['alt_text']}for m in media],ensure_ascii=False))
