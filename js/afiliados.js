/* Eventos de clique de saída nos botões de afiliado — GoatCounter, sem cookie.
 *
 * Convenção: aff/{programa}/{pagina}
 *   aff/segurospromo/home
 *   aff/viator/destinos/buenos-aires
 *   aff/viator/passeios/buenos-aires   (distingue a vitrine da página de orçamento)
 *
 * Pega qualquer <a data-aff="...">, inclusive os que ainda nem existem — botão novo
 * é rastreado sozinho, sem tocar neste arquivo.
 */
(function () {
  "use strict";

  function pagina() {
    var p = (location.pathname || "/").replace(/^\/+|\/+$/g, "");
    return p === "" ? "home" : p;
  }

  function acharBotao(alvo) {
    // sem closest() em navegador antigo: sobe na árvore na unha
    for (var n = alvo; n && n.nodeType === 1; n = n.parentNode) {
      if (n.tagName === "A" && n.getAttribute("data-aff")) return n;
    }
    return null;
  }

  document.addEventListener("click", function (e) {
    try {
      var botao = acharBotao(e.target);
      if (!botao) return;
      var gc = window.goatcounter;
      if (!gc || typeof gc.count !== "function") return;   // bloqueador ativo: só não conta
      var programa = botao.getAttribute("data-aff");
      gc.count({
        path: "aff/" + programa + "/" + pagina(),
        title: "Clique afiliado: " + programa,
        event: true
      });
    } catch (err) {
      /* métrica nunca pode atrapalhar a navegação do leitor */
    }
  }, true);
})();
