#!/usr/bin/env python3
"""Gera um addon de catalogos estaticos do Stremio sem dependencias extras.
Rodar: python gerar_catalogos.py
Para expandir Oscar usando dataset aberto: python gerar_catalogos.py --importar-oscar
"""
from pathlib import Path
import csv, json, re, sys, urllib.request
ROOT=Path(__file__).resolve().parent
CSV=ROOT/'dados'/'vencedores.csv'
OUT=ROOT/'docs'
IDS={
    'oscar_melhor_filme':('movie','Oscar — Melhor Filme · Vencedores'),
    'emmy_drama':('series','Emmy — Drama · Vencedores'),
    'emmy_comedia':('series','Emmy — Comédia · Vencedores'),
    'emmy_limitada':('series','Emmy — Série Limitada · Vencedores'),
}
DATASET='https://raw.githubusercontent.com/holmesredding/movieawardsdata/main/oscar-nominations.json'

def ler_csv():
    with CSV.open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def salvar_csv(rows):
    with CSV.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['categoria','ano_cerimonia','ano_obra','titulo','imdb_id','fonte']);w.writeheader();w.writerows(rows)

def ano_cerimonia(ano):
    if '/' in ano:
        a,b=ano.split('/')
        if ano=='1927/28': return 1929
        if ano=='1928/29': return 1930
        return int(a[:2]+b)
    return int(ano)+1

def importar_historico_oscar(rows):
    print('Baixando dados historicos do Oscar. Internet necessaria...')
    req=urllib.request.Request(DATASET,headers={'User-Agent':'PremiadosStremio/1.0'})
    with urllib.request.urlopen(req,timeout=35) as r: dados=json.load(r)
    existentes={(r['categoria'],int(r['ano_cerimonia'])) for r in rows}
    adicionados=0
    for item in dados:
        if item.get('category')!='Best Picture' or item.get('won') is not True: continue
        year=ano_cerimonia(str(item['year']))
        if ('oscar_melhor_filme',year) in existentes: continue
        movies=item.get('movies') or []
        if len(movies)!=1: continue
        m=movies[0]; imdb=str(m.get('imdb_id') or '')
        if not re.fullmatch(r'tt\d{7,10}',imdb): continue
        rows.append(dict(categoria='oscar_melhor_filme',ano_cerimonia=str(year),ano_obra='',titulo=m['title'],imdb_id=imdb,fonte=DATASET))
        existentes.add(('oscar_melhor_filme',year));adicionados+=1
    salvar_csv(rows)
    print(f'{adicionados} vencedores historicos adicionados ao arquivo CSV.')
    return rows

def gerar(rows):
    manifesto=dict(id='org.premiados.oscar.emmy.winners',version='1.0.0',
      name='Premiados — Oscar e Emmy',
      description='Somente vencedores de Melhor Filme do Oscar e das principais categorias de series do Emmy, em ordem da cerimonia mais recente para a mais antiga. Nao fornece videos.',
      resources=['catalog'],types=['movie','series'],
      catalogs=[{'type':typ,'id':id_,'name':label} for id_,(typ,label) in IDS.items()])
    (OUT/'manifest.json').write_text(json.dumps(manifesto,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    total=0
    for categoria,(typ,label) in IDS.items():
        selecao=[r for r in rows if r['categoria']==categoria]
        selecao.sort(key=lambda r:int(r['ano_cerimonia']),reverse=True)
        y=[];ids=[]
        for r in selecao:
            imdb=r['imdb_id'].strip()
            if not re.fullmatch(r'tt\d{7,10}',imdb):
                raise ValueError(f'IMDb ID invalido: {r}')
            ident=(int(r['ano_cerimonia']),imdb)
            if ident in ids: raise ValueError(f'Duplicata: {r}')
            ids.append(ident);y.append(int(r['ano_cerimonia']))
            # The item's IMDb ID is retained for Cinemeta and other addons.
            # If a show won for consecutive years, Stremio might visually merge items.
            
        metas=[dict(id=r['imdb_id'].strip(),type=typ,name=f"{r['ano_cerimonia']} · {r['titulo']}",
            poster=f"https://images.metahub.space/poster/medium/{r['imdb_id'].strip()}/img",posterShape='poster')
            for r in selecao]
        destino=OUT/'catalog'/typ
        destino.mkdir(parents=True,exist_ok=True)
        (destino/(categoria+'.json')).write_text(json.dumps({'metas':metas},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(f'{label}: {len(metas)} registros ({min(y) if y else "?"}–{max(y) if y else "?"})')
        total+=len(metas)
    print('Total:',total,'registros. Arquivos prontos em docs/')

if __name__=='__main__':
    rows=ler_csv()
    if '--importar-oscar' in sys.argv:
        try: rows=importar_historico_oscar(rows)
        except Exception as e: print(f'Falha ao baixar historico (mantendo CSV atual): {e}')
    gerar(rows)
