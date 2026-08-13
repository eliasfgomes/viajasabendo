# -*- coding: utf-8 -*-
"""Mantém frescos os preços dos cards de passeio das PÁGINAS DE DESTINO.

As vitrines (`/passeios/*`) são geradas inteiras pelo `gerar_vitrine.py`. Já as
páginas de orçamento (`/destinos/*`) são escritas à mão e tinham o preço fixo no
HTML — ou seja, envelheciam sozinhas. Como o site vende confiança em número,
preço velho é o pior defeito possível.

Este script não precisa de marcação especial: ele acha cada card `.passeio`,
extrai o código do produto do próprio link do Viator e reescreve só o parágrafo
de preço, no formato padrão da casa.

  sem oferta:  R$ 280,00 por pessoa · preço de 13 de agosto de 2026 — confira o de hoje
  com oferta:  R$ 341 a 371 por pessoa · faixa vista em 13 de agosto de 2026: em oferta
               no nosso levantamento, cheio na página do produto

Uso:  python _tools/atualizar_precos_paginas.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_vitrine import ESTADO, brl, brl_curto, data_br  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CARD = re.compile(r'<div class="passeio">.*?(?=<div class="passeio">|</div>\s*</div>)', re.S)
COD = re.compile(r'viator\.com[^"]*?/d\d+-(\w+)\?')
PRECO = re.compile(r'<p class="passeio-preco">.*?</p>', re.S)

# ZONAS PROTEGIDAS — a conta de cada viagem é fechada e datada à mão, casando com o
# vídeo que a anuncia. Este script só pode mexer no preço dos CARDS de passeio.
# Se um dia um bug fizer ele encostar na tabela, na resposta rápida ou no total,
# o arquivo NÃO é gravado. Roda sem ninguém olhando: a regra tem que ser trava, não cuidado.
PROTEGIDAS = [
    re.compile(r'<table class="custos">.*?</table>', re.S),   # tabela do orçamento
    re.compile(r'<div class="resposta[^"]*">.*?</div>', re.S),  # resposta rápida e box do erro
]


def zonas_protegidas(html: str) -> list[str]:
    return [t for p in PROTEGIDAS for t in p.findall(html)]


def paragrafo(p: dict) -> str:
    unidade = "pelo grupo (tour privado)" if "PRIVATE_TOUR" in (p.get("selos") or []) else "por pessoa"
    quando = data_br(p.get("visto_em", ""))
    if p.get("preco_cheio"):
        valor = "%s a %s" % (brl_curto(p["preco"]), brl_curto(p["preco_cheio"]))
        nota = ("faixa vista em %s: em oferta no nosso levantamento, cheio na página do produto" % quando)
    else:
        valor = brl(p["preco"])
        nota = "preço de %s — confira o de hoje" % quando
    return '<p class="passeio-preco">%s %s <em>· %s</em></p>' % (valor, unidade, nota)


def main() -> int:
    if not ESTADO.exists():
        print("[precos] estado do vigia não encontrado:", ESTADO)
        return 0
    estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    trocados = ausentes = 0

    for arq in sorted((RAIZ / "destinos").glob("*/index.html")):
        html = original = arq.read_text(encoding="utf-8")
        for card in CARD.findall(html):
            mcod = COD.search(card)
            mpreco = PRECO.search(card)
            if not mcod or not mpreco:
                continue
            codigo = mcod.group(1)
            produto = estado.get(codigo)
            if not produto or produto.get("preco") is None:
                print("  [!] %s: %s não está no estado do vigia (preço fica como está)"
                      % (arq.parent.name, codigo))
                ausentes += 1
                continue
            novo_card = card.replace(mpreco.group(0), paragrafo(produto))
            if novo_card != card:
                html = html.replace(card, novo_card)
                trocados += 1
        if html != original:
            if zonas_protegidas(html) != zonas_protegidas(original):
                print("  [ABORTADO] %s: a atualização encostou na tabela/resposta rápida — "
                      "arquivo NÃO gravado" % arq.relative_to(RAIZ))
                continue
            arq.write_text(html, encoding="utf-8", newline="\n")
            print("  atualizado:", arq.relative_to(RAIZ))

    print("[precos] %d cards com preço atualizado · %d produtos fora do vigia" % (trocados, ausentes))
    if ausentes:
        print("[precos] dica: produto fora do vigia = destino que falta na watchlist "
              "(_tools/vigia/watchlist.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
