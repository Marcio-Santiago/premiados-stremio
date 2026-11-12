#!/usr/bin/env python3
"""Constrói os catálogos estáticos de Premiados, sem instalar dependências.
Não modifica IDs ou páginas de detalhes, e não oferece streams.
"""
from pathlib import Path
import csv, json, re, sys

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'dados' / 'vencedores.csv'
DOCS = ROOT / 'docs'
COLS = ['categoria', 'ano_cerimonia', 'ano_obra', 'titulo', 'imdb_id', 'fonte']
CATALOGOS = [
 ('oscar_melhor_filme', 'movie', 'Oscar — Melhor Filme · Vencedores'),
 ('oscar_internacional', 'movie', 'Oscar — Filme Internacional · Vencedores'),
 ('oscar_roteiro_original', 'movie', 'Oscar — Roteiro Original · Vencedores'),
 ('oscar_roteiro_adaptado', 'movie', 'Oscar — Roteiro Adaptado · Vencedores'),
 ('oscar_animacao', 'movie', 'Oscar — Animação · Vencedores'),
 ('emmy_drama', 'series', 'Emmy — Drama · Vencedores'),
 ('emmy_comedia', 'series', 'Emmy — Comédia · Vencedores'),
 ('emmy_limitada', 'series', 'Emmy — Série Limitada · Vencedores'),
]


def carregar():
    with BASE.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def salvar(linhas):
    BASE.parent.mkdir(parents=True, exist_ok=True)
    with BASE.open('w', encoding='utf-8-sig', newline='') as f:
        w=csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(linhas)


def gerar(linhas=None):
    linhas = carregar() if linhas is None else linhas
    tipos = {k: t for k,t,_ in CATALOGOS}
    declarados=set(tipos)
    if set(r['categoria'] for r in linhas) - declarados:
        raise ValueError('CSV contém categoria não prevista no manifesto.')
    for r in linhas:
        if not re.fullmatch(r'tt\d{7,10}',r['imdb_id'].strip()):
            raise ValueError('IMDb inválido: '+str(r))
        if not 1920 < int(r['ano_cerimonia']) <= 2026:
            raise ValueError('Ano inválido: '+str(r))
    DOCS.mkdir(exist_ok=True)
    manifest = {
       'id':'org.premiados.oscar.emmy.winners',  # não trocar: preserva instalação antiga
       'version':'1.1.1',
       'name':'Premiados — Oscar e Emmy',
       'description':'Vencedores das 5 categorias do Oscar e 3 do Emmy, por ano da premiação, do mais novo ao mais antigo. Não fornece vídeos.',
       'resources':['catalog'], 'types':['movie','series'],
       'catalogs':[{'type':t,'id':k,'name':n} for k,t,n in CATALOGOS]
    }
    (DOCS/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    total=0
    for cat,typ,nome in CATALOGOS:
        subset = sorted((r for r in linhas if r['categoria']==cat),key=lambda r:int(r['ano_cerimonia']),reverse=True)
        keys=set()
        for r in subset:
            key = (r['ano_cerimonia'],r['imdb_id'])
            if key in keys: raise ValueError(f'Duplicata na categoria {cat}: {key}')
            keys.add(key)
        metas=[{
          'id':r['imdb_id'].strip(), 'type':typ,
          'name':f"{r['ano_cerimonia']} · {r['titulo']}",
          'poster':f"https://images.metahub.space/poster/medium/{r['imdb_id'].strip()}/img",
          'posterShape':'poster'
        } for r in subset]
        target=DOCS/'catalog'/typ
        target.mkdir(parents=True,exist_ok=True)
        (target/(cat+'.json')).write_text(json.dumps({'metas':metas},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'{nome}: {len(metas)} itens '+(f'({subset[-1]["ano_cerimonia"]}–{subset[0]["ano_cerimonia"]})' if subset else ''))
        total += len(metas)
    print(f'TOTAL: {total} prêmios, {len(CATALOGOS)} catálogos')
    return total

if __name__=='__main__':
    gerar()
