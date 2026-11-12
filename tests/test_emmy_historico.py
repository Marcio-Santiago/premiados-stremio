"""Evita regressões de cobertura dos Emmys antes de 2000."""
import sys, csv, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from atualizar_historico import popular_emmy

def ler_csv(caminho):
    with caminho.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

class EmmyHistoricoTest(unittest.TestCase):
    def test_dados_anteriores_a_2000(self):
        linhas=ler_csv(ROOT/'dados'/'emmy_historico_pre2000.csv')
        anos_comedia={int(x['ano_cerimonia']) for x in linhas if x['categoria']=='emmy_comedia'}
        anos_limitada={int(x['ano_cerimonia']) for x in linhas if x['categoria']=='emmy_limitada'}
        self.assertEqual(anos_comedia,set(range(1952,2000)))
        self.assertEqual(anos_limitada,set(range(1973,2000)))
        self.assertEqual(len(linhas),76) # incluindo dois vencedores históricos de 1957
        sem_id={(x['categoria'],int(x['ano_cerimonia'])) for x in linhas if not x['imdb_id']}
        self.assertEqual(sem_id,{('emmy_limitada',1984),('emmy_limitada',1999)})

    def test_mesma_serie_ganhando_varios_anos_e_idempotencia(self):
        linhas=ler_csv(ROOT/'dados'/'emmy_historico_pre2000.csv')
        antigos=ler_csv(ROOT/'dados'/'vencedores.csv')
        novos,pend=popular_emmy(antigos,online=False)
        self.assertTrue(any(x['categoria']=='emmy_comedia' and x['ano_cerimonia']=='1952' for x in novos+antigos))
        self.assertTrue(any(x['categoria']=='emmy_limitada' and x['ano_cerimonia']=='1973' for x in novos+antigos))
        self.assertTrue(any(x['categoria']=='emmy_comedia' and x['ano_cerimonia']=='1998' for x in novos+antigos))
        self.assertTrue(any(x['categoria']=='emmy_limitada' and x['ano_cerimonia']=='1998' for x in novos+antigos))
        adicionados=antigos+novos
        novos2,_=popular_emmy(adicionados,online=False)
        self.assertEqual(novos2,[])

if __name__=='__main__': unittest.main()
