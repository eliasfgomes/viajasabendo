# -*- coding: utf-8 -*-
"""Roda o vigia de preços e regenera as vitrines. É o que a Action executa todo dia.

Contrato com o workflow (regra da OPERACAO): **falha de API sai com 0 e sem tocar em
nada** — o site nunca quebra por causa do vigia. Só quando a varredura dá certo é que
as páginas são regeneradas; o commit fica a cargo do workflow, e só se houver diff.

Uso:  python _tools/atualizar_vitrines.py
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atualizar_precos_paginas  # noqa: E402
import gerar_vitrine             # noqa: E402
import vigia_viator              # noqa: E402

DESTINOS = ["buenos-aires", "foz-do-iguacu"]
MIN_CARDS = 4                 # vitrine com menos que isso é sinal de dado ruim


def main() -> int:
    # 1) varredura — qualquer problema aqui encerra sem mexer em arquivo nenhum
    try:
        r = vigia_viator.rodar()
    except vigia_viator.ErroAPI as e:
        print(f"[vigia] API indisponível: {e}")
        print("[vigia] nada foi alterado — o site continua com os preços da última leitura boa.")
        return 0
    except Exception:                                   # bug nosso, não da API
        print("[vigia] erro inesperado — nada foi alterado:")
        traceback.print_exc()
        return 0

    print(f"[vigia] {r['varridos']} produtos varridos · {r['produtos']} acompanhados")
    for a in r["alertas"]:
        print("  ALERTA:", a)

    # 2) regenera as vitrines a partir do estado novo
    for slug in DESTINOS:
        try:
            caminho, n = gerar_vitrine.monta(slug)
            if n < MIN_CARDS:
                print(f"[vitrine] {slug}: só {n} cards (< {MIN_CARDS}) — dado suspeito, revisar")
        except Exception:
            print(f"[vitrine] falhou ao gerar {slug}:")
            traceback.print_exc()
            return 0                                    # não commita meia atualização

    # 3) refresca os preços dos cards nas páginas de destino (escritas à mão)
    try:
        atualizar_precos_paginas.main()
    except Exception:
        print("[precos] falhou ao atualizar as páginas de destino:")
        traceback.print_exc()
        return 0

    print("[ok] vitrines e páginas de destino com os preços de hoje.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
