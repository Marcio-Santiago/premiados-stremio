import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from gerar_catalogos import gerar, carregar, CATALOGOS
from atualizar_historico import extrair_emmy, extrair_oscar, cerimonia, mapear_oscar

class PremiacaoTest(unittest.TestCase):
    def test_manifesto_e_recurso(self):
        total=gerar()
        self.assertGreaterEqual(total,100)
        import json
        m=json.loads((ROOT/'docs'/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(len(m['catalogs']),8)
        self.assertEqual(m['id'],'org.premiados.oscar.emmy.winners')
        for cat,tipo,_ in CATALOGOS:
            p=ROOT/'docs'/'catalog'/tipo/(cat+'.json')
            dados=json.loads(p.read_text(encoding='utf-8'))['metas']
            anos=[int(it['name'][:4]) for it in dados]
            self.assertEqual(anos,sorted(anos,reverse=True))
            self.assertTrue(all(it['id'].startswith('tt') for it in dados))

    def test_anos_oscars_inicio(self):
        self.assertEqual(cerimonia('1927/28'),1929)
        self.assertEqual(cerimonia('1928/29'),1930)
        self.assertEqual(cerimonia('1932/33'),1934)
        self.assertEqual(cerimonia('2025'),2026)

    def test_sem_prêmios_indicados(self):
        doc=[{'category':'Best Picture','year':'1994','won':False,'movies':[{'title':'Pulp Fiction','imdb_id':'tt0110912'}]},
             {'category':'Best Picture','year':'1994','won':True,'movies':[{'title':'Forrest Gump','imdb_id':'tt0109830'}]}]
        res=extrair_oscar(doc)
        self.assertEqual(len(res),1)
        self.assertEqual(res[0]['ano_cerimonia'],'1995')

    def test_emmy_tabela_respeita_anos(self):
        html='<table><tr><th>Year</th><th>Winner</th><th>Network</th></tr>' + ''.join(
            f'<tr><td>{y}</td><td><strong>The Show</strong> beat 3 others <ul><li>Not winner</li></ul></td><td>NBC</td></tr>' for y in range(1951,2000))+'</table>'
        res=extrair_emmy(html)
        self.assertEqual(len(res),49)
        self.assertEqual(res[0],(1951,'The Show',True))

if __name__=='__main__': unittest.main()
