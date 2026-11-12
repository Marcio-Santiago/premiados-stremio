# 🏆 Premiados — Oscar e Emmy | preparacao da versão 1.0 completa

**Funciona com o mesmo ID** do protótipo já instalado no Stremio:
`org.premiados.oscar.emmy.winners`.

## Os oito catálogos

**Oscar:** Melhor Filme; Melhor Filme Internacional; Melhor Roteiro Original; Melhor Roteiro Adaptado; Melhor Animação.
**Emmy:** Melhor Série Dramática; Melhor Série de Comédia; Melhor Minissérie / Série Limitada.

Os catálogos estão em ordem de cerimônia decrescente. Apenas vencedores. As páginas dos títulos, sinopses e fontes de reprodução continuam sendo providas pelo Stremio e pelos demais addons.

## Estado do pacote

Este é um **pacote de preparação**, ainda não um histórico completo: os arquivos `docs/` incluídos contêm **118 registros com IMDb**, incluindo todos os vencedores do Emmy das categorias Drama e Comédia entre 2000 e 2026, e as séries/minisséries identificadas entre 2000 e 2026 (não inclui dois telefilmes historicamente premiados em categorias combinadas). Cinco catálogos Oscar estão presentes, mas as categorias novas têm inicialmente 2024–2026. O script online importa dados históricos e resolve registros adicionais; títulos não associados com segurança a um ID IMDb ficam em `dados/pendencias.csv`. As categorias históricas podem ter intervalos não premiados ou mudanças de nome. O resultado completo precisa ser auditado, especialmente Emmy pré-2000.

**Não indique 'histórico completo' enquanto o relatório de cobertura e as pendências não forem conferidos.**

## 1. Publicar os arquivos no mesmo GitHub

1. **Faça um backup** do repositório atual `premiados-stremio` (Code → Download ZIP).
2. Extraia este ZIP. Não mande este arquivo ZIP fechado para o GitHub.
3. Acesse seu repositório existente → **Add file → Upload files** e envie o conteúdo extraído, preservando `docs/`, `dados/`, `scripts/`, `tests/` e `.github/workflows/` na raiz. Arquivos que já existem devem ser substituídos, não duplicados em uma nova subpasta.
4. Confirme que `docs/manifest.json` está dentro de `docs` (não na raiz) e salve em **Commit changes**.
5. GitHub Pages deve continuar em **Settings → Pages → Deploy from a branch → main → /docs**. Não precisa criar novo repositório nem trocar o endereço do addon.
6. O Stremio deve reconhecer os oito catálogos da versão `1.1.0`. Pode ser necessário atualizar a página, reiniciar o Stremio ou reinstalar o manifesto para atualizar a lista de catálogos.

## 2. Importar o máximo possível do histórico pelo GitHub (sem instalar Python no seu PC)

1. Abra o repositório no GitHub e clique em **Actions**.
2. No menu lateral, clique em **Importar vencedores históricos**.
3. Clique em **Run workflow → Run workflow** (branch `main`).
4. Abra a execução e confira se as etapas ficam verdes. O fluxo baixa os dados públicos e salva os CSVs e JSONs de catálogos no **mesmo** repositório. O GitHub Pages publica esses arquivos a partir de `/docs`.
5. Verifique o arquivo `dados/pendencias.csv` antes de dizer que o acervo está completo.

Se `git push` do workflow falhar com `403 Resource not accessible by integration`, entre em **Settings → Actions → General → Workflow permissions** e habilite `Read and write permissions` *se as políticas da sua conta permitirem*. Não forneça senhas ou tokens ao addon.

Se uma fonte mudar de formato ou a internet falhar, o fluxo interrompe a publicação em vez de inventar dados. Veja os erros em **Actions**.

## Arquivos importantes

- `docs/manifest.json`: identificação oficial e oito catálogos.
- `docs/catalog/movie/` e `docs/catalog/series/`: listas do Stremio.
- `dados/vencedores.csv`: prêmio, ano da cerimônia, título e IMDb.
- `dados/pendencias.csv`: registros sem identificação segura para revisão.
- `dados/emmy_2000_2025.csv`: referência adicional para os três catálogos do Emmy.
- `scripts/atualizar_historico.py`: importação do histórico do Oscar e Emmy, com checagem de IMDb.
- `scripts/gerar_catalogos.py`: regeneração dos arquivos estáticos do Stremio.
- `tests/test_catalogos.py`: testes locais.

## Fontes, limitações e créditos

- Oscar oficial: https://awardsdatabase.oscars.org/
- Emmy oficial: https://www.televisionacademy.com/awards/awards-search
- JSON acadêmico de premiações (MIT © Zac Delventhal), até 2023 ou ano disponível: https://github.com/holmesredding/movieawardsdata
- Catálogos históricos do Emmy usados como apoio: https://envelopeparty.com/data/emmys
- Metadados e identificação de séries: https://v3-cinemeta.strem.io/
- Protocolo de addons do Stremio: https://github.com/Stremio/stremio-addon-sdk/blob/master/docs/protocol.md

As listas são informações factuais dos premiados; os sites originais mantêm seus próprios direitos sobre apresentação, imagens e textos. O pacote não reproduz sinopses, conteúdos audiovisuais ou páginas protegidas. Não fornece vídeos ou formas de contornar assinaturas.

**Histórico de categorias:** as primeiras cerimônias do Oscar tiveram regras diferentes; o prêmio competitivo de filme internacional começou após as premiações honorárias. Os prêmios históricos de *história original* não são automaticamente classificados como *roteiro original*. O Emmy também renomeou e dividiu categorias ao longo das décadas. Verifique os intervalos e vencedores antes de considerar o histórico definitivo.
