# Gera as texturas do jogo pela API de imagens da OpenAI.
# Lê texturas/prompts.json ({"nome": {"prompt": "...", "tamanho": "1024x1024"}}), gera só as que ainda não existem
# em texturas/png/ e para no teto MAX por rodada (para não haver surpresa na fatura). A chave vem do segredo OPENAI.
import json, os, sys, base64, urllib.request, urllib.error, time, traceback
K = os.environ.get('OPENAI_API_KEY', '').strip()
base0 = os.path.dirname(os.path.abspath(__file__))
if not K:
    open(os.path.join(base0, 'log.txt'), 'a').write(time.strftime('%Y-%m-%d %H:%M') + ' SEM CHAVE: o segredo OPENAI nao chegou na rotina\n')
    print('Falta o segredo OPENAI'); sys.exit(0)
MODELO = os.environ.get('MODELO') or 'gpt-image-1.5'
QUAL = os.environ.get('QUALIDADE') or 'medium'
MAX = 40
base = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(base, 'prompts.json'), encoding='utf-8'))
out = os.path.join(base, 'png'); os.makedirs(out, exist_ok=True)
log = open(os.path.join(base, 'log.txt'), 'a', encoding='utf-8')
feitas = 0
for nome, d in P.items():
    alvo = os.path.join(out, nome + '.png')
    if os.path.exists(alvo): continue
    if feitas >= MAX: print('teto da rodada atingido'); break
    corpo = json.dumps({'model': MODELO, 'prompt': d['prompt'], 'size': d.get('tamanho', '1024x1024'), 'quality': QUAL, 'n': 1}).encode()
    req = urllib.request.Request('https://api.openai.com/v1/images/generations', data=corpo,
        headers={'Authorization': 'Bearer ' + K, 'Content-Type': 'application/json'})
    for tent in range(3):
        try:
            r = json.load(urllib.request.urlopen(req, timeout=300))
            b64 = r['data'][0].get('b64_json')
            if not b64:
                url = r['data'][0]['url']; img = urllib.request.urlopen(url, timeout=120).read()
            else:
                img = base64.b64decode(b64)
            open(alvo, 'wb').write(img); feitas += 1
            print('ok', nome); log.write(f'{time.strftime("%Y-%m-%d %H:%M")} ok {nome} {MODELO} {QUAL}\n'); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='ignore')[:300]
            print('erro', nome, e.code, msg); log.write(f'erro {nome} {e.code} {msg}\n')
            if e.code in (400, 401, 403): break
            time.sleep(10)
        except Exception as e:
            print('erro', nome, e); log.write(f'erro {nome} {e}\n'); time.sleep(10)
print('geradas nesta rodada:', feitas)
