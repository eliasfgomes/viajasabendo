/* Alterna a página entre "sozinho" e "em casal".
 *
 * O modo já vem definido pelo script do <head> (que lê ?modo=casal antes de pintar,
 * para não piscar o número errado). Aqui só tratamos o clique no seletor:
 *   - troca o data-modo do <html> (o CSS faz o resto)
 *   - atualiza a URL sem recarregar, para o link compartilhado preservar o modo
 *   - ajusta aria-pressed e o <title>
 *
 * O modo também entra no evento de clique de afiliado (js/afiliados.js), então dá
 * para saber se quem clicou no eSIM estava vendo a conta de casal ou a de sozinho.
 */
(function () {
  "use strict";

  var TITULOS = {
    sozinho: "Quanto custa 7 dias em Buenos Aires em 2026 (viajando sozinho) | Viaja Sabendo",
    casal: "Quanto custa 7 dias em Buenos Aires em 2026 (em casal) | Viaja Sabendo"
  };

  var raiz = document.documentElement;
  var botoes = document.querySelectorAll("[data-modo-btn]");
  if (!botoes.length) return;

  function aplicar(modo, mexerNaUrl) {
    raiz.setAttribute("data-modo", modo);
    for (var i = 0; i < botoes.length; i++) {
      var b = botoes[i];
      b.setAttribute("aria-pressed", b.getAttribute("data-modo-btn") === modo ? "true" : "false");
    }
    if (TITULOS[modo]) document.title = TITULOS[modo];
    if (mexerNaUrl && window.history && history.replaceState) {
      try {
        var u = new URL(location.href);
        if (modo === "casal") u.searchParams.set("modo", "casal");
        else u.searchParams.delete("modo");
        history.replaceState(null, "", u.pathname + (u.search || "") + u.hash);
      } catch (e) {}
    }
  }

  for (var i = 0; i < botoes.length; i++) {
    botoes[i].addEventListener("click", function (e) {
      aplicar(e.currentTarget.getAttribute("data-modo-btn"), true);
    });
  }

  // sincroniza o estado inicial (o <head> pode ter posto casal pela URL)
  aplicar(raiz.getAttribute("data-modo") === "casal" ? "casal" : "sozinho", false);
})();
