(() => {
  document.querySelectorAll('.research-theme').forEach((theme) => {
    const summary = theme.querySelector('summary');
    theme.addEventListener('keydown', (event) => {
      if (event.key !== 'Escape') return;
      theme.open = false;
      summary.focus();
    });
  });

  const bibliography = document.querySelector('.research-bibliography');
  if (!bibliography) return;

  const controls = bibliography.querySelectorAll('[data-bib-panel]');
  controls.forEach((button) => {
    const panel = document.getElementById(button.dataset.bibPanel);
    if (!panel) return;
    panel.hidden = true;
    button.hidden = false;
    button.addEventListener('click', () => {
      const open = panel.hidden;
      const entry = button.closest('.bib-entry');
      entry.querySelectorAll('[data-bib-panel]').forEach((other) => {
        document.getElementById(other.dataset.bibPanel).hidden = true;
        other.setAttribute('aria-expanded', 'false');
      });
      panel.hidden = !open;
      button.setAttribute('aria-expanded', String(open));
    });
  });

  const revealLinkedPaper = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (error) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target || !bibliography.contains(target)) return;
    const disclosure = target.closest('details');
    if (disclosure) disclosure.open = true;
    if (target.classList.contains('bib-entry__panel')) {
      target.hidden = false;
      controls.forEach((button) => {
        if (button.dataset.bibPanel === id) button.setAttribute('aria-expanded', 'true');
      });
    }
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
  };
  window.addEventListener('hashchange', revealLinkedPaper);
  revealLinkedPaper();
})();
