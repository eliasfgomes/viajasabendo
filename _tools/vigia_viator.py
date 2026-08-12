# -*- coding: utf-8 -*-
"""Vigia de preços Viator — versão do SITE (roda no GitHub Actions).

Cópia adaptada de `fabrica_modular/vigia/vigia_viator.py` (stdlib puro). Diferenças
feitas de propósito para rodar na nuvem sem derrubar o site:

  1. A chave vem de `VIATOR_API_KEY` no ambiente (secret do Actions). Se não houver,
     tenta o `.secrets/.env` local — assim o mesmo arquivo roda na máquina do Elias.
  2. Falha de API NÃO chama sys.exit: levanta `ErroAPI`, e quem chama decide.
     No CI a decisão é sempre: não mexer em nada e sair com 0.
  3. Estado e watchlist moram em `_tools/vigia/` dentro do repo do site.

REGRA DETERMINÍSTICA (verificada em 10/ago/2026 nos 7 produtos de BA): quando o feed
traz `preco_cheio`, a LANDING cobra o cheio — a promoção do feed não vale na página.
Por isso o preço real considerado nos alertas é `preco_cheio or preco`.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.error
import urllib.request

try:  # SSL do Norton na máquina local; no runner do GitHub não existe e não faz falta
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
DIR_VIGIA = os.path.join(BASE, "vigia")
ENV_LOCAL = r"C:\Users\elias\.secrets\.env"
API = "https://api.viator.com/partner"
LIMIAR_QUEDA = 0.15
ARQ_WATCH = os.path.join(DIR_VIGIA, "watchlist.json")
ARQ_ESTADO = os.path.join(DIR_VIGIA, "estado.json")
ARQ_REL = os.path.join(DIR_VIGIA, "relatorio_ultimo.md")


class ErroAPI(RuntimeError):
    """Qualquer problema de rede/chave/HTTP com a API do Viator."""


def chave_api() -> str:
    k = (os.environ.get("VIATOR_API_KEY") or "").strip()
    if k:
        return k
    if os.path.exists(ENV_LOCAL):
        with open(ENV_LOCAL, encoding="utf-8-sig") as f:
            for ln in f:
                ln = ln.strip()
                if ln.startswith("VIATOR_API_KEY"):
                    return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise ErroAPI("VIATOR_API_KEY ausente (secret do Actions ou .secrets/.env)")


def chamada(caminho: str, corpo: dict) -> dict:
    req = urllib.request.Request(
        API + caminho,
        data=json.dumps(corpo).encode("utf-8"),
        method="POST",
        headers={
            "exp-api-key": chave_api(),
            "Accept": "application/json;version=2.0",
            "Accept-Language": "pt-BR",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", errors="replace")[:300]
        raise ErroAPI(f"HTTP {e.code} em {caminho}: {detalhe}") from e
    except Exception as e:  # timeout, DNS, TLS…
        raise ErroAPI(f"{type(e).__name__} em {caminho}: {e}") from e


def _melhor_imagem(p: dict):
    """URL da capa em ~600px — é o que a vitrine do site usa."""
    for img in (p.get("images") or [])[:1]:
        variantes = sorted(
            (v for v in (img.get("variants") or []) if v.get("url")),
            key=lambda v: abs((v.get("width") or 0) - 600),
        )
        if variantes:
            return variantes[0]["url"]
    return None


def busca_produtos(dest_id, quantos: int = 20) -> list[dict]:
    d = chamada(
        "/products/search",
        {
            "filtering": {"destination": str(dest_id)},
            "pagination": {"start": 1, "count": quantos},
            "currency": "BRL",
        },
    )
    saida = []
    for p in (d.get("products") or d.get("results") or []):
        preco = ((p.get("pricing") or {}).get("summary") or {})
        rev = p.get("reviews") or {}
        saida.append({
            "codigo": p.get("productCode"),
            "titulo": (p.get("title") or "?")[:90],
            "preco": preco.get("fromPrice"),
            "preco_cheio": preco.get("fromPriceBeforeDiscount"),
            "moeda": (p.get("pricing") or {}).get("currency", "BRL"),
            "nota": rev.get("combinedAverageRating"),
            "reviews": rev.get("totalReviews"),
            "selos": p.get("flags") or [],
            "url": p.get("productUrl"),
            "imagem": _melhor_imagem(p),
        })
    return saida


def rodar(top_n: int = 6) -> dict:
    """Varre a watchlist e grava estado + relatório. Levanta ErroAPI se a API falhar.

    Só escreve em disco DEPOIS de todas as chamadas terem dado certo — assim uma
    falha no meio da varredura não deixa estado pela metade.
    """
    if not os.path.exists(ARQ_WATCH):
        raise ErroAPI(f"watchlist.json nao existe em {ARQ_WATCH}")
    with open(ARQ_WATCH, encoding="utf-8") as f:
        watch = json.load(f)
    estado = {}
    if os.path.exists(ARQ_ESTADO):
        with open(ARQ_ESTADO, encoding="utf-8") as f:
            estado = json.load(f)

    hoje = datetime.date.today().isoformat()
    alertas: list[str] = []
    linhas = [f"# Vigia Viator — {hoje}", ""]
    estado_novo = dict(estado)
    varridos = 0

    for dest in watch.get("destinos", []):
        nome, dest_id = dest.get("nome"), dest.get("id")
        if not dest_id:
            linhas += [f"## {nome} — SEM destId na watchlist", ""]
            continue
        produtos = busca_produtos(dest_id, int(watch.get("produtos_por_destino", 20)))
        varridos += len(produtos)
        linhas.append(f"## {nome} (destId {dest_id}) — {len(produtos)} produtos varridos")
        for c in sorted(produtos, key=lambda x: x.get("reviews") or 0, reverse=True)[:top_n]:
            linhas.append(
                f"- {c['titulo']} — R$ {c['preco']} · nota {c['nota']} ({c['reviews']} reviews)"
                + (f" · SELOS: {','.join(c['selos'])}" if c["selos"] else "")
            )
        linhas.append("")

        for p in produtos:
            cod = p.get("codigo")
            if not cod:
                continue
            antes = estado.get(cod)
            if antes:
                real_ant = antes.get("preco_cheio") or antes.get("preco")
                real_novo = p.get("preco_cheio") or p.get("preco")
                if real_ant and real_novo and real_novo < real_ant * (1 - LIMIAR_QUEDA):
                    alertas.append(
                        f"QUEDA {100 * (1 - real_novo / real_ant):.0f}% NA LANDING: {p['titulo']} "
                        f"({nome}) R$ {real_ant} -> R$ {real_novo} · {p.get('url')}"
                    )
                novo_selo = ("SPECIAL_OFFER" in p.get("selos", [])
                             and "SPECIAL_OFFER" not in (antes.get("selos") or []))
                if novo_selo:
                    if p.get("preco_cheio"):
                        alertas.append(
                            f"OFERTA SÓ NO FEED (landing cobra R$ {p['preco_cheio']} — não usar em "
                            f"pauta/Promote): {p['titulo']} ({nome})"
                        )
                    else:
                        alertas.append(
                            f"OFERTA NOVA (sem preco_cheio → landing deve bater): {p['titulo']} "
                            f"({nome}) R$ {p.get('preco')} · {p.get('url')}"
                        )
                r_ant, r_novo = antes.get("reviews") or 0, p.get("reviews") or 0
                if r_novo - r_ant >= int(watch.get("limiar_reviews", 30)):
                    alertas.append(
                        f"DEMANDA SUBINDO: {p['titulo']} ({nome}) +{r_novo - r_ant} avaliações"
                    )
            p2 = dict(p)
            p2["visto_em"] = hoje
            p2["destino"] = nome
            estado_novo[cod] = p2

    if not varridos:
        raise ErroAPI("a API respondeu, mas nenhum produto voltou — não vou sobrescrever o estado")

    linhas.insert(2, "## 🔔 ALERTAS" if alertas else "## (sem alertas nesta leitura)")
    for i, a in enumerate(alertas):
        linhas.insert(3 + i, f"- {a}")

    os.makedirs(DIR_VIGIA, exist_ok=True)
    with open(ARQ_ESTADO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(estado_novo, f, ensure_ascii=False, indent=1)
    with open(ARQ_REL, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(linhas) + "\n")
    return {"produtos": len(estado_novo), "varridos": varridos, "alertas": alertas}


if __name__ == "__main__":
    try:
        r = rodar()
    except ErroAPI as e:
        print(f"[vigia] FALHOU: {e}")
        sys.exit(1)
    print(f"[vigia] {r['varridos']} varridos · {r['produtos']} acompanhados · {len(r['alertas'])} alertas")
    for a in r["alertas"]:
        print("  !", a)
