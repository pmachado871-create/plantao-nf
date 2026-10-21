# Robô de dublagem: gera cada fala na ElevenLabs e monta os pacotes vox_*.js que o jogo carrega.
import json,os,sys,time,base64,urllib.request,urllib.error,collections
KEY=os.environ.get('ELEVENLABS_API_KEY','').strip()
if not KEY:sys.exit('Falta o segredo ELEVENLABS_API_KEY nas configurações do repositório.')
F=json.load(open('vozes/falas.json'));V=json.load(open('vozes/vozes.json'));os.makedirs('vozes/mp3',exist_ok=True)
LIM=int(os.environ.get('LIMITE','0') or 0)  # 0 = sem limite de caracteres nesta rodada
feitos=0;gastos=0;erros=0
for k,(txt,papel,pack) in F.items():
  mp='vozes/mp3/'+k+'.mp3'
  if os.path.exists(mp):continue
  if LIM and gastos+len(txt)>LIM:print('Limite desta rodada atingido.');break
  body=json.dumps({'text':txt,'model_id':V.get('modelo','eleven_multilingual_v2'),'voice_settings':{'stability':0.5,'similarity_boost':0.75}}).encode()
  url='https://api.elevenlabs.io/v1/text-to-speech/%s?output_format=mp3_22050_32'%V[papel]
  for tent in range(6):
    req=urllib.request.Request(url,data=body,headers={'xi-api-key':KEY,'Content-Type':'application/json','Accept':'audio/mpeg'})
    try:
      with urllib.request.urlopen(req,timeout=90) as r:open(mp,'wb').write(r.read())
      feitos+=1;gastos+=len(txt);break
    except urllib.error.HTTPError as e:
      msg=e.read().decode(errors='ignore')[:300]
      if e.code==429:time.sleep(10*(tent+1));continue
      if e.code in(401,402) or 'quota' in msg:print('Parando: créditos ou permissão da ElevenLabs ->',e.code,msg);LIM=-1;break
      print('Erro',e.code,k,msg);erros+=1;break
    except Exception as e:print('Falha de rede',k,e);time.sleep(5)
  if LIM==-1:break
  time.sleep(0.3)
print('Geradas nesta rodada:',feitos,'| caracteres:',gastos,'| erros:',erros)
by=collections.defaultdict(dict)
for k,(txt,papel,pack) in F.items():
  mp='vozes/mp3/'+k+'.mp3'
  if os.path.exists(mp):by[pack][k]='data:audio/mpeg;base64,'+base64.b64encode(open(mp,'rb').read()).decode()
for pack,d in by.items():
  n='vox_'+pack;open(n+'.js','w').write('window.__VOX=Object.assign(window.__VOX||{},'+json.dumps(d)+');(window.__VOXLOADED=window.__VOXLOADED||{})["'+n+'"]=1;')
tot=len(F);ok=sum(len(d) for d in by.values());print('Total pronto: %d de %d falas'%(ok,tot))
