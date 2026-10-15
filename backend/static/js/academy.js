/* Read-only progressive lesson tools. No eval, network, storage or grading. */
(() => {
  'use strict';
  const filter = document.getElementById('module-filter');
  if (filter) {
    const cards = Array.from(document.querySelectorAll('[data-module-card]'));
    const status = document.getElementById('module-filter-status');
    filter.addEventListener('input', () => {
      const query = filter.value.trim().toLocaleLowerCase();
      let count = 0;
      for (const card of cards) {
        card.hidden = !card.textContent.toLocaleLowerCase().includes(query);
        if (!card.hidden) count += 1;
      }
      status.textContent = `${count} matching module${count === 1 ? '' : 's'}`;
    });
  }
  for (const trace of document.querySelectorAll('[data-trace]')) {
    const rows = Array.from(trace.querySelectorAll('tbody tr'));
    const button = trace.querySelector('[data-trace-next]');
    const status = trace.querySelector('[data-trace-status]');
    let step = -1;
    button.hidden = false;
    button.addEventListener('click', () => {
      step = (step + 1) % rows.length;
      rows.forEach((row, index) => {
        row.classList.toggle('academy-current-step', index === step);
        if (index === step) row.setAttribute('aria-current', 'step');
        else row.removeAttribute('aria-current');
      });
      status.textContent = `Step ${step + 1} of ${rows.length}: ${rows[step].textContent.trim().replace(/\s+/g, ' ')}`;
      button.textContent = step === rows.length - 1 ? 'Restart trace' : 'Next trace step';
    });
  }
  for (const button of document.querySelectorAll('.academy-copy')) {
    button.addEventListener('click', async () => {
      const code = button.previousElementSibling;
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = 'Copied';
      } catch (_) {
        button.textContent = 'Copy unavailable — select code manually';
      }
    });
  }
  const form = document.getElementById('academy-attempt');
  if (form) {
    const reference = document.getElementById('academy-solution');
    const status = document.getElementById('academy-attempt-status');
    const code = document.getElementById('academy-code');
    reference.hidden = true;
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (!code.value.trim()) {
        status.textContent = 'Write an attempted approach or code before comparing the reference.';
        code.focus();
        return;
      }
      reference.hidden = false;
      status.textContent = 'Attempt noted in this tab only. Nothing was run, graded or saved. Open the reference to compare your reasoning.';
      reference.querySelector('summary').focus();
    });
    form.addEventListener('reset', () => {
      reference.open = false;
      reference.hidden = true;
      status.textContent = 'Draft cleared. Retry locally; no previous attempt was saved by this page.';
    });
  }
})();
