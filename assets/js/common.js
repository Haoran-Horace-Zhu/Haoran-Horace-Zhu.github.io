$(document).ready(function () {
  // add toggle functionality to publication titles, award and bibtex buttons
  $("button.article-title-toggle, a.abstract").click(function () {
    const $item = $(this).closest(".pub-list-item");
    const $abstract = $item.find(".abstract.hidden").first();
    const willOpen = !$abstract.hasClass("open");

    $abstract.toggleClass("open", willOpen);
    $item.find(".article-title-toggle, a.abstract").attr("aria-expanded", willOpen);
    $item.find(".award.hidden.open, .bibtex.hidden.open").removeClass("open");
  });
  $("a.award").click(function () {
    const $item = $(this).closest(".pub-list-item");
    $item.find(".abstract.hidden.open, .bibtex.hidden.open").removeClass("open");
    $item.find(".article-title-toggle, a.abstract").attr("aria-expanded", false);
    $item.find(".award.hidden").toggleClass("open");
  });
  $("a.bibtex").click(function () {
    const $item = $(this).closest(".pub-list-item");
    $item.find(".abstract.hidden.open, .award.hidden.open").removeClass("open");
    $item.find(".article-title-toggle, a.abstract").attr("aria-expanded", false);
    $item.find(".bibtex.hidden").toggleClass("open");
  });
  $("a").removeClass("waves-effect waves-light");

  // bootstrap-toc
  if ($("#toc-sidebar").length) {
    // remove related publications years from the TOC
    $(".publications h2").each(function () {
      $(this).attr("data-toc-skip", "");
    });
    var navSelector = "#toc-sidebar";
    var $myNav = $(navSelector);
    Toc.init($myNav);
    $("body").scrollspy({
      target: navSelector,
    });
  }

  // add css to jupyter notebooks
  const cssLink = document.createElement("link");
  cssLink.href = "../css/jupyter.css";
  cssLink.rel = "stylesheet";
  cssLink.type = "text/css";

  let jupyterTheme = determineComputedTheme();

  $(".jupyter-notebook-iframe-container iframe").each(function () {
    $(this).contents().find("head").append(cssLink);

    if (jupyterTheme == "dark") {
      $(this).bind("load", function () {
        $(this).contents().find("body").attr({
          "data-jp-theme-light": "false",
          "data-jp-theme-name": "JupyterLab Dark",
        });
      });
    }
  });

  // trigger popovers
  $('[data-toggle="popover"]').popover({
    trigger: "hover",
  });
});
