document.querySelectorAll('.flash').forEach((flash) => {
  setTimeout(() => flash.classList.add('fade-out'), 4200);
});

document.querySelectorAll('[data-confirm]').forEach((element) => {
  element.addEventListener('submit', (event) => {
    if (!window.confirm(element.dataset.confirm)) event.preventDefault();
  });
});
