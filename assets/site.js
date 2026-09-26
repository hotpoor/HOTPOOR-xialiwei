const timeline = document.querySelector('#timeline');
const controls = [...document.querySelectorAll('[data-scroll]')];
if (timeline) {
  const update = () => controls.forEach(button => {
    button.disabled = Number(button.dataset.scroll) < 0
      ? timeline.scrollLeft <= 1
      : timeline.scrollLeft >= timeline.scrollWidth - timeline.clientWidth - 1;
  });
  controls.forEach(button => button.addEventListener('click', () => {
    timeline.scrollBy({left: Number(button.dataset.scroll) * timeline.clientWidth * 0.7,
      behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
  }));
  timeline.addEventListener('scroll', update, {passive: true});
  window.addEventListener('resize', update);
  const current = timeline.querySelector('[aria-current]');
  if (current) timeline.scrollLeft = current.parentElement.offsetLeft - timeline.firstElementChild.offsetLeft;
  update();
}
