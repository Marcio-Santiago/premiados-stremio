#!/usr/bin/env python3
"""Reúne vencedores de fontes públicas e publica os que têm IMDb ID verificável.
Uso local (sem rede): python scripts/atualizar_historico.py --offline
Uso completo:       python scripts/atualizar_historico.py --online
NÃO inventa ID: gera dados/pendencias.csv para revisão.
"""
from pathlib import Path
import argparse, csv, difflib, json, re, sys, time, unicodedata
from urllib.request import urlopen, Request
from urllib.parse import quote
from bs4 import BeautifulSoup
from gerar_catalogos import ROOT, carregar, salvar, gerar

OSCARS_JSON='https://raw.githubusercontent.com/holmesredding/movieawardsdata/main/oscar-nominations.json'
EMMY_PAGES={
 'emmy_drama':'https://envelopeparty.com/data/emmys/drama-series',
 'emmy_comedia':'https://envelopeparty.com/data/emmys/comedy-series',
 'emmy_limitada':'https://envelopeparty.com/data/emmys/limited-series',
}
A_FONTE='https://www.oscars.org/oscars/ceremonies/'
E_FONTE='https://www.televisionacademy.com/awards/nominees-winners/'


def ler_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))


def obter(url,timeout=45):
    erro=None
    for i in range(3):
        try:
            req=Request(url,headers={'User-Agent':'PremiadosStremio/1.1 (+https://github.com/Stremio/stremio-addon-sdk)','Accept':'application/json, text/html;q=0.9,*/*;q=0.8'})
            with urlopen(req,timeout=timeout) as r: return r.read()
        except Exception as exc:
            erro=exc
            time.sleep(1+i*2)
    raise RuntimeError(f'Falha ao obter {url}: {erro}')


def normal(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(ch for ch in s if not unicodedata.combining(ch))
    s=s.casefold().replace('&','and')
    s=re.sub(r'[^a-z0-9]+',' ',s).strip()
    return re.sub(r'^the\s+','',s)


def cerimonia(oscar_year):
    ano=str(oscar_year).strip()
    if ano=='1927/28': return 1929
    if ano in ('1928/29','1929/30'): return 1930
    if ano=='1930/31': return 1931
    if ano=='1931/32': return 1932
    if ano=='1932/33': return 1934
    return int(ano)+1


def mapear_oscar(c):
    n=normal(c)
    if n=='best picture': return 'oscar_melhor_filme'
    if n in ('best international feature film','best foreign language film'):
        return 'oscar_internacional'
    if n=='best animated feature': return 'oscar_animacao'
    if n in ('best original screenplay','best original story and screenplay','best story and screenplay written directly for the screen'):
        return 'oscar_roteiro_original'
    if n in ('best adapted screenplay','best screenplay based on material from another medium','best screenplay based on material previously produced or published'):
        return 'oscar_roteiro_adaptado'
    # Prêmios históricos distintos (ex.: Best Original Story, Best Story, Best Screenplay)
    # não devem ser classificados à força como roteiro original/adaptado.
    return None


def extrair_oscar(documento):
    linhas=[]
    for item in documento:
        if not item.get('won'): continue
        categoria=mapear_oscar(str(item.get('category','')))
        if not categoria: continue
        try: ano=cerimonia(item.get('year'))
        except (TypeError,ValueError): continue
        if ano>2026 or ano<1929: continue
        movies=item.get('movies') or []
        if len(movies)!=1: continue
        m=movies[0]
        imdb=m.get('imdb_id')
        if not isinstance(imdb,str) or not re.fullmatch(r'tt\d{7,10}',imdb): continue
        title=str(m.get('title') or '').strip()
        if not title: continue
        linhas.append(dict(categoria=categoria,ano_cerimonia=str(ano),ano_obra=str(item['year']),titulo=title,imdb_id=imdb,fonte=OSCARS_JSON))
    return linhas


def extrair_emmy(html):
    """Extrai registros de anos reais de tabela, não a lista de indicados."""
    soup=BeautifulSoup(html,'html.parser')
    tabela=None
    for t in soup.find_all('table'):
        hd=' '.join(th.get_text(' ',strip=True) for th in t.find_all('th'))
        if 'year' in hd.lower() and 'winner' in hd.lower(): tabela=t;break
    if tabela is None:
        raise ValueError('A tabela de vencedores do Emmy mudou de formato; nenhuma extração foi feita.')
    rows=[]
    for tr in tabela.find_all('tr'):
        cols=tr.find_all('td',recursive=False)
        if len(cols)<2:continue
        year_text=cols[0].get_text(' ',strip=True)
        m=re.search(r'(19\d\d|20\d\d)',year_text)
        if not m: continue
        ano=int(m.group(1))
        val=cols[1]
        # Primeiro elemento textual da célula é o vencedor, antes dos indicados em lista.
        for ul in val.find_all(['ul','ol','details','button']): ul.decompose()
        texto=val.get_text(' ',strip=True)
        nao_verificado=bool(re.search(r'\bunverified\b',texto,re.I))
        texto=re.sub(r'\s+(?:repeat\s+)?(?:unverified\s+)?beat\s+\d+\s+others.*$','',texto,flags=re.I).strip()
        texto=re.sub(r'\s+(?:repeat|unverified)\s*$','',texto,flags=re.I).strip()
        if texto and 1950<=ano<=2025:
            rows.append((ano,texto,not nao_verificado))
    if len(rows)<35:
        raise ValueError('Poucos anos extraídos do Emmy: '+str(len(rows)))
    return rows


class Resolver:
    def __init__(self,known):
        self.known={normal(r['titulo']):r['imdb_id'] for r in known if r.get('titulo') and r.get('imdb_id')}
        self.known.update({normal(r['titulo']):r['imdb_id'] for r in ler_csv(ROOT/'dados'/'imdb_series_confirmados.csv')})
        self.cache={}
        self.alt={
            normal('The People v. O. J. Simpson: American Crime Story'):'American Crime Story',
            normal('The Assassination of Gianni Versace: American Crime Story'):'American Crime Story',
            normal('The White Lotus'):'The White Lotus',
        }

    def buscar(self,titulo,ano):
        key=normal(titulo)
        if key in self.known:return self.known[key]
        if key in self.cache:return self.cache[key]
        q=self.alt.get(key,titulo)
        url='https://v3-cinemeta.strem.io/catalog/series/top/search='+quote(q,safe='')+'.json'
        try:
            metas=json.loads(obter(url,timeout=20)).get('metas',[])
        except Exception:
            self.cache[key]=None;return None
        cand=[]
        for m in metas:
            imdb=m.get('imdb_id') or m.get('id','')
            if not isinstance(imdb,str) or not re.fullmatch(r'tt\d{7,10}',imdb):continue
            n=normal(m.get('name',''))
            score=difflib.SequenceMatcher(None,normal(q),n).ratio()
            if not n or not (score>=0.88 or n==normal(q)):continue
            start=m.get('releaseInfo') or m.get('year') or ''
            yy=re.search(r'(19\d\d|20\d\d)',str(start))
            if yy:
                diff=ano-int(yy.group(1))
                if diff<0:score-=0.25
                elif diff>45:score-=0.15
                else:score+=0.06
            cand.append((score,imdb,m.get('name')))
        cand.sort(reverse=True)
        chosen=(cand[0][1] if cand and cand[0][0]>=.88 and (len(cand)<2 or cand[0][0]-cand[1][0]>.07 or cand[0][1]==cand[1][1]) else None)
        self.cache[key]=chosen
        return chosen


def consolidar(linhas,novas):
    # Mantém múltiplas vitórias de uma mesma categoria em 1930 (duas cerimônias).
    keys={(r['categoria'],r['ano_cerimonia'],r['imdb_id']) for r in linhas}
    total=0
    for r in novas:
        k=(r['categoria'],r['ano_cerimonia'],r['imdb_id'])
        if k not in keys:
            linhas.append(r);keys.add(k);total+=1
    return total


def popular_emmy(linhas, online):
    """Usa base histórica auditada para 1952–1999; nunca inventa IMDb ID.

    A base local evita perder épocas antigas por mudanças de layout em sites.
    Para títulos sem identificador seguro, mantém uma pendência visível.
    """
    pend=[]
    novos=[]
    resolver=Resolver(linhas)
    base=ler_csv(ROOT/'dados'/'emmy_2000_2025.csv')
    caminho_historico=ROOT/'dados'/'emmy_historico_pre2000.csv'
    if caminho_historico.exists():
        base.extend(ler_csv(caminho_historico))
    else:
        print('AVISO: falta dados/emmy_historico_pre2000.csv',file=sys.stderr)

    existe_ano={(r['categoria'],r['ano_cerimonia']) for r in linhas}
    existe_exato={(r['categoria'],r['ano_cerimonia'],r['imdb_id']) for r in linhas}
    for r in base:
        cat=r['categoria']
        ano=str(r['ano_cerimonia'])
        nome=r['titulo']
        yr=int(ano)
        imdb=(r.get('imdb_id') or '').strip()
        # Em 1957 havia dois prêmios gerais por duração, registrados separadamente.
        permite_mais_uma=(cat=='emmy_comedia' and yr==1957)
        if imdb and (cat,ano,imdb) in existe_exato:
            continue
        if not permite_mais_uma and (cat,ano) in existe_ano:
            continue
        motivo=(r.get('observacao_historica') or '')
        # Não trocar um título histórico ambíguo por outra produção em busca automática.
        if not imdb and yr<2000:
            pend.append(dict(categoria=cat,ano_cerimonia=ano,titulo=nome,
                         motivo=motivo or 'IMDb da obra premiada ainda não confirmado'))
            continue
        if cat=='emmy_limitada' and nome in ('Behind the Candelabra','Game Change'):
            pend.append(dict(categoria=cat,ano_cerimonia=ano,titulo=nome,
                motivo='Telefilme em categoria temporariamente combinada; não é uma minissérie'))
            continue
        if not imdb:
            imdb=resolver.buscar(nome,yr) if online else resolver.known.get(normal(nome))
        if not imdb:
            pend.append(dict(categoria=cat,ano_cerimonia=ano,titulo=nome,
                         motivo='IMDb não resolvido com segurança'))
            continue
        novo=dict(categoria=cat,ano_cerimonia=ano,ano_obra='',titulo=nome,imdb_id=imdb,
                  fonte=(E_FONTE+ano if yr<2000 else E_FONTE+ano))
        novos.append(novo)
        existe_ano.add((cat,ano))
        existe_exato.add((cat,ano,imdb))
    return novos,pend

def salvar_pendencias(pend):
    p=ROOT/'dados'/'pendencias.csv'
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['categoria','ano_cerimonia','titulo','motivo'])
        w.writeheader(); w.writerows(sorted(pend,key=lambda r:(r['categoria'],-int(r['ano_cerimonia']))))


def main():
    args=argparse.ArgumentParser()
    flag=args.add_mutually_exclusive_group(required=True)
    flag.add_argument('--online',action='store_true',help='Baixa a base histórica do Oscar e consulta Emmy/Cinemeta')
    flag.add_argument('--offline',action='store_true',help='Aplica apenas os vencedores do Emmy com IMDb já catalogados')
    opt=args.parse_args()
    rows=carregar()
    if opt.online:
        print('Lendo a base histórica de vencedores do Oscar...')
        doc=json.loads(obter(OSCARS_JSON))
        add=consolidar(rows,extrair_oscar(doc))
        print('Oscar: registros novos =',add)
        if sum(r['categoria'].startswith('oscar_') for r in rows)<170:
            raise RuntimeError('Base histórica do Oscar incompleta (<170 registros totais). Nenhum CSV será sobrescrito.')
    extras,pend=popular_emmy(rows,opt.online)
    adicionados=consolidar(rows,extras)
    print('Emmy: registros adicionados =',adicionados)
    salvar(rows)
    salvar_pendencias(pend)
    total=gerar(rows)
    print('Pendências IMDb:',len(pend))
    if opt.online and total<250:
        raise RuntimeError('Resultado muito pequeno: verificar fontes antes de publicar.')

if __name__=='__main__': main()
