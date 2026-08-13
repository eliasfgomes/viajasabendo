# viajasabendo.com.br

Site estático do **Viaja Sabendo** (braço-site do TikTok @viajasabendo). HTML+CSS puro, sem
build, sem JS. Hospedagem alvo: **GitHub Pages** (grátis) com domínio próprio.

## Estrutura

```
index.html                      home
checklist-europa/               checklist Europa 2026 (ETIAS/EES/seguro) — é O link da série sem-visto
destinos/<slug>/index.html      páginas "quanto custa" (foz-do-iguacu, fernando-de-noronha,
                                jericoacoara, chapada-dos-veadeiros)
sobre/  privacidade/  404.html  institucionais
css/style.css                   único CSS (mobile-first)
CNAME  robots.txt  sitemap.xml  infra Pages/SEO
```

Novo destino = copiar uma pasta de `destinos/`, trocar conteúdo, adicionar `<url>` no
`sitemap.xml` e card na home. Header/nav e footer são duplicados em cada página (site pequeno;
se passar de ~10 páginas, criar gerador).

## Links de afiliado

Todo link de parceiro tem `class="btn-aff"` + `data-aff="<parceiro>"` + `rel="noopener sponsored"`
+ `target="_blank"`. **Link sem o parâmetro de afiliado rende R$ 0** — foi o que aconteceu com o
Seguros Promo até 11/ago/2026. Antes de publicar qualquer botão novo, confira se o código está lá.

| data-aff       | Parceiro       | Programa                         | Status | Parâmetro que PRECISA estar no href |
|----------------|----------------|----------------------------------|--------|--------------------------------------|
| `segurospromo` | Seguros Promo  | Parceiros Promo (10–25%)         | ✅ ativo | `pcrid=14823` |
| `holafly`      | Holafly eSIM   | Impact (10% venda / 8–25% assinatura, janela 30d) | ✅ ativo | domínio `holafly.sjv.io` |
| `viator`       | Viator         | próprio (passeios)               | ✅ ativo | `pid=P00312237` |
| `rentcars`     | RentCars       | próprio (até 50% da comissão)    | ✅ ativo | `requestorid=10950` |
| `civitatis`    | Civitatis      | próprio, 8–10% + €1/free tour    | ❌ removido do site em 13/ago (nunca aprovado; link cru rendia R$ 0) | — |

**Regra que ficou:** nenhum link de saída sem atribuição. Onde o Viator não cobre o destino
(a Chapada dos Veadeiros não existe no catálogo deles), a página aponta para o **canal oficial
da atração** — que é mais barato para o leitor — em vez de um afiliado que não paga.

Conferir tudo de uma vez:
```bash
grep -rn "data-aff" --include="*.html" .        # todos os pontos
grep -rn "segurospromo" --include="*.html" . | grep -c pcrid   # tem que bater com o total
```

## ⚠️ O repositório tem um segundo autor: o vigia commita sozinho

O workflow `.github/workflows/vigia_precos.yml` roda **todo dia às 08:20 BRT**, atualiza os preços
do Viator e **commita direto no `main`** (autor `vigia-precos`) sempre que algo muda. Consequência
prática para quem trabalha aqui:

```bash
git pull --rebase origin main      # SEMPRE antes de começar e antes de empurrar
```

O que ele toca (e só isso): `_tools/vigia/estado.json`, `_tools/vigia/relatorio_ultimo.md` e as
páginas `passeios/*/index.html`. **Não edite as vitrines à mão** — elas são geradas; mexa no
`_tools/gerar_vitrine.py` (texto/curadoria) e rode `python _tools/atualizar_vitrines.py`.

Se a API do Viator estiver fora, o workflow avisa, **sai com 0 e não commita nada** — o site fica
com a última leitura boa. Isso é por design: métrica ou preço nunca derruba a página.

## Deploy (GitHub Pages) — passos do Elias

1. Criar repo **público** `viajasabendo` em github.com/eliasfgomes (Pages grátis exige repo
   público em conta free). NÃO commitar segredo nenhum aqui — é vitrine pública.
2. Nesta pasta: `git remote add origin https://github.com/eliasfgomes/viajasabendo.git`
   e `git push -u origin main`.
3. No repo: Settings → Pages → Source = branch `main`, pasta `/ (root)`. O arquivo `CNAME`
   já configura o domínio.
4. **DNS no registro.br** (Painel → domínio → DNS → editar zona), criar:
   - 4 registros **A** para o domínio raiz (`viajasabendo.com.br`):
     `185.199.108.153` · `185.199.109.153` · `185.199.110.153` · `185.199.111.153`
   - 1 **CNAME**: `www` → `eliasfgomes.github.io`
5. Esperar propagar (minutos a ~1h), voltar em Settings → Pages e marcar **Enforce HTTPS**
   (o certificado Let's Encrypt é emitido sozinho).

## Pendências pós-v1 (por ordem)

- [ ] Trocar hrefs `data-aff` pelos links com código conforme aprovações
- [ ] Foto real por destino (Pexels/Freepik licenciado) no lugar do layout texto-first
- [ ] E-mail de contato público (decidir qual) na página Sobre — redes sociais cobrem por ora
- [ ] Pixel TikTok / medição de clique (só depois que houver link de afiliado ativo)
- [ ] Páginas novas puxadas pelos vídeos que performarem (1 vídeo forte → 1 página)
