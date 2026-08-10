# -*- coding: utf-8 -*-
"""Gera as paginas de vitrine de passeios a partir do vigia de precos.

Fonte: C:\\Users\\elias\\fabrica_modular\\vigia\\estado.json (campos preco,
preco_cheio, nota, reviews, selos, url com pid, imagem, visto_em).

REGRA DE PRECO (verificada em 10/ago/2026, 7 produtos): quando o produto tem
`preco_cheio` preenchido (ou seja, esta marcado como oferta no feed), a pagina
do Viator cobra o PRECO CHEIO. Nesses casos publicamos FAIXA (feed -> cheio),
nunca so o promocional — senao o leitor clica e ve outro numero.

Uso:  python _tools/gerar_vitrine.py buenos-aires
"""
from __future__ import annotations
import json, sys, html
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = Path(r"C:\Users\elias\fabrica_modular\vigia\estado.json")
NOTA_MINIMA = 4.5          # mesmo piso de qualidade da curadoria
REVIEWS_MINIMO = 100

# Nome curto e legenda de cada produto (o titulo do feed e longo demais pro card)
CATALOGO = {
    "buenos-aires": {
        "titulo_pagina": "Os passeios que valem em Buenos Aires",
        "descricao": "Os passeios mais bem avaliados de Buenos Aires, com foto, nota, número de avaliações e preço do dia. Ordenados por volume de avaliações.",
        "volta_para": ("/destinos/buenos-aires/", "Quanto custa 7 dias em Buenos Aires"),
        "produtos": [
            ("208148P1", "Tour gastronômico em Palermo", "Parrilla, empanada e vinho com guia — o passeio mais avaliado da cidade.", "Mesa de comidas argentinas num tour gastronômico em Palermo"),
            ("203530P1", "City tour privado com guia local", "A cidade inteira no seu ritmo, com guia só para o seu grupo.", "Vista do obelisco de Buenos Aires em city tour privado"),
            ("11143P1", "City tour em grupo pequeno", "La Boca, San Telmo, Recoleta e Puerto Madero num roteiro só.", "Casas coloridas do Caminito, em La Boca, Buenos Aires"),
            ("422114P1", "Aula de culinária argentina", "Você cozinha e janta o que fez: empanadas, carne na grelha e alfajor.", "Empanadas sendo preparadas em aula de culinária argentina"),
            ("5653P5", "Show de tango íntimo", "Sala pequena, dançarinos a poucos metros. Não inclui jantar.", "Casal dançando tango em sala intimista de Buenos Aires"),
            ("11143P3", "Dia numa estância gaúcha", "Asado, cavalgada e destreza gaúcha a duas horas da cidade.", "Gaúchos a cavalo numa estância argentina"),
            ("11143P2", "Delta do Tigre com catamarã", "Meio dia de rio, casas sobre palafitas e feira de artesanato.", "Casas de madeira sobre palafitas no delta do Tigre"),
        ],
    },
    "foz-do-iguacu": {
        "titulo_pagina": "Os passeios que valem em Foz do Iguaçu",
        "descricao": "Os passeios mais bem avaliados de Foz do Iguaçu, com foto, nota, número de avaliações e preço do dia. Ordenados por volume de avaliações.",
        "volta_para": ("/destinos/foz-do-iguacu/", "Quanto custa 4 dias em Foz do Iguaçu"),
        "produtos": [
            ("2484P236", "Os dois lados em um dia", "Brasil de manhã, Argentina à tarde — o mais avaliado da cidade.", "Cataratas do Iguaçu vistas da passarela do lado brasileiro"),
            ("384147P6", "Dois lados em grupo pequeno", "Mesmo roteiro, grupo menor e o preço mais baixo da lista.", "Grupo pequeno diante das quedas das Cataratas do Iguaçu"),
            ("384147P1", "Dois lados com guia privado", "Só o seu grupo, no seu ritmo, sem esperar ninguém.", "Guia acompanhando visitantes nas Cataratas do Iguaçu"),
            ("216404P1", "Voo panorâmico de helicóptero", "Dez minutos vendo a Garganta do Diabo de cima.", "Helicóptero sobrevoando as Cataratas do Iguaçu"),
            ("7558P4", "Só o lado argentino, com transfer", "Para quem já fez o lado brasileiro: o transporte cruza a fronteira.", "Passarela sobre as quedas no parque argentino do Iguazú"),
            ("409882P1", "Dia completo nos dois lados", "A alternativa em grupo para o roteiro clássico de um dia.", "Arco-íris sobre as quedas das Cataratas do Iguaçu"),
        ],
    },
}

CABECA = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} — fotos, notas e preços | Viaja Sabendo</title>
<meta name="description" content="{descricao}">
<link rel="canonical" href="https://viajasabendo.com.br/passeios/{slug}/">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descricao}">
<meta property="og:type" content="website">
<meta property="og:url" content="https://viajasabendo.com.br/passeios/{slug}/">
<link rel="preconnect" href="https://media-cdn.tripadvisor.com">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>

<header class="topo">
  <div class="topo-inner">
    <a class="logo" href="/">Viaja<span>Sabendo</span></a>
    <nav class="menu">
      <a href="/">Início</a>
      <a href="/checklist-europa/">Checklist Europa</a>
      <a href="/sobre/">Sobre</a>
    </nav>
  </div>
</header>

<main>
<article class="conteudo">
  <span class="selo">Preços e notas conferidos em {data_br}</span>
  <h1 class="titulo">{titulo}</h1>
  <p>Escolhidos pelo que o viajante já comprovou: só entram passeios com <strong>nota {nota_min} ou mais</strong> e pelo menos <strong>100 avaliações</strong>, na ordem de quem tem mais gente avaliando. Todos com cancelamento grátis.</p>
  <p class="aviso-parceiro">Os botões desta página são links de parceiro: reservando por eles, o site recebe comissão sem custo extra para você. O preço mostrado é o do dia da conferência — confira o de hoje antes de fechar.</p>

  <div class="vitrine">
{cards}
  </div>

  <p><a class="btn" href="{volta_url}">← {volta_txt}</a></p>

  <div class="nota">
    Notas, número de avaliações, fotos e preços vêm das páginas oficiais dos produtos, conferidos em {data_br}. Passeio marcado com faixa de preço (ex.: "R$ 336 a 365") é produto que aparece em oferta no nosso levantamento mas cuja página pode cobrar o valor cheio — mostramos os dois para você não ser surpreendido no clique.
  </div>
</article>
</main>

<footer class="rodape">
  <div class="rodape-inner">
    <div>
      <strong>Viaja Sabendo</strong><br>
      Viaje sabendo quanto custa — não descobrindo na hora.<br>
      <a href="https://www.tiktok.com/@viajasabendo" rel="noopener" target="_blank">TikTok</a> ·
      <a href="https://www.instagram.com/viajasabendo" rel="noopener" target="_blank">Instagram</a> ·
      <a href="https://www.youtube.com/@viajasabendo" rel="noopener" target="_blank">YouTube</a>
    </div>
    <div>
      <a href="/sobre/">Sobre o projeto</a><br>
      <a href="/privacidade/">Privacidade e parceiros</a><br>
      <a href="/termos/">Termos de uso</a><br>
      <a href="/contato/">Contato</a><br>
      <a href="/">Todos os destinos</a>
    </div>
    <div class="disclosure">
      Aviso de transparência: o Viaja Sabendo participa de programas de afiliados. Reservas feitas pelos links do site podem gerar comissão, sem custo adicional para o leitor. Valores citados são estimativas na data indicada em cada página — confira sempre o preço vigente antes de comprar.<br><br>
      © 2026 Viaja Sabendo · viajasabendo.com.br
    </div>
  </div>
</footer>

<script data-goatcounter="https://viajasabendo.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
"""

CARD = """    <div class="vcard">
      <img src="{imagem}" alt="{alt}" width="540" height="360" loading="{loading}" decoding="async" referrerpolicy="no-referrer-when-downgrade">
      <div class="vcard-corpo">
        <h2>{nome}</h2>
        <div class="vcard-meta"><span class="nota">★ {nota}</span><span>{reviews} avaliações</span>{selo}</div>
        <p>{legenda}</p>
        <p class="vcard-preco">{preco}<small>{unidade} · {ressalva}</small></p>
        <a class="btn-aff" data-aff="viator" href="{url}" rel="noopener sponsored" target="_blank">Ver disponibilidade</a>
      </div>
    </div>"""


def brl(v: float) -> str:
    return ("R$ %.2f" % v).replace(".", ",")


def brl_curto(v: float) -> str:
    return "R$ " + format(int(round(v)), ",d").replace(",", ".")


def monta(slug: str) -> str:
    cfg = CATALOGO[slug]
    dados = json.loads(ESTADO.read_text(encoding="utf-8"))
    cards, data_vista, pulados = [], None, []

    for i, (codigo, nome, legenda, alt) in enumerate(cfg["produtos"]):
        p = dados.get(codigo)
        if not p:
            pulados.append((codigo, "não está no estado.json")); continue
        if p.get("nota", 0) < NOTA_MINIMA or p.get("reviews", 0) < REVIEWS_MINIMO:
            pulados.append((codigo, "reprovado no piso: %.2f / %s avaliações" % (p.get("nota", 0), p.get("reviews", 0))))
            continue
        data_vista = p.get("visto_em", data_vista)
        cheio = p.get("preco_cheio")
        if cheio:   # oferta no feed -> a landing cobra o cheio: publica FAIXA
            preco = "%s a %s" % (brl_curto(p["preco"]), brl_curto(cheio))
            ressalva = "faixa: em oferta no levantamento, cheio na página"
        else:
            preco = brl(p["preco"])
            ressalva = "preço de %s" % data_br(p.get("visto_em", ""))
        selo = ""
        if "SPECIAL_OFFER" in p.get("selos", []):
            selo = '<span class="selo-oferta">Em oferta</span>'
        # tour privado e cobrado POR GRUPO — rotular "por pessoa" seria errado
        unidade = "pelo grupo (tour privado)" if "PRIVATE_TOUR" in p.get("selos", []) else "por pessoa"
        cards.append(CARD.format(
            imagem=html.escape(p["imagem"], quote=True),
            alt=html.escape(alt, quote=True),
            loading="eager" if i == 0 else "lazy",
            nome=html.escape(nome), legenda=html.escape(legenda),
            nota=("%.2f" % p["nota"]).replace(".", ",")[:4],
            reviews=format(p["reviews"], ",d").replace(",", "."),
            selo=selo, preco=preco, ressalva=ressalva, unidade=unidade,
            url=html.escape(p["url"], quote=True)))

    pagina = CABECA.format(
        titulo=cfg["titulo_pagina"], descricao=cfg["descricao"], slug=slug,
        data_br=data_br(data_vista or ""), nota_min="4,5",
        cards="\n".join(cards),
        volta_url=cfg["volta_para"][0], volta_txt=cfg["volta_para"][1])

    destino = RAIZ / "passeios" / slug / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(pagina, encoding="utf-8", newline="\n")
    print("gerado:", destino, "|", len(cards), "cards")
    for c, motivo in pulados:
        print("  PULADO", c, "-", motivo)
    return str(destino)


MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def data_br(iso: str) -> str:
    try:
        a, m, d = iso.split("-")
        return "%d de %s de %s" % (int(d), MESES[int(m) - 1], a)
    except Exception:
        return iso or "—"


if __name__ == "__main__":
    monta(sys.argv[1] if len(sys.argv) > 1 else "buenos-aires")
