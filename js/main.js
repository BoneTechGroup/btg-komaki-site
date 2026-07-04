/* BTG接骨院 小牧院 共通スクリプト */

/* スクロール出現アニメ */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

/* ヘッダー：スクロールで影 */
const hd = document.querySelector('header');
addEventListener('scroll', () => {
  hd && hd.classList.toggle('scrolled', scrollY > 10);
}, { passive: true });

/* ハンバーガーメニュー */
const hamb = document.querySelector('.hamb');
const mnav = document.querySelector('.mnav');
if (hamb && mnav) {
  hamb.addEventListener('click', () => {
    hamb.classList.toggle('open');
    mnav.classList.toggle('open');
    document.body.style.overflow = mnav.classList.contains('open') ? 'hidden' : '';
  });
  mnav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
    hamb.classList.remove('open'); mnav.classList.remove('open');
    document.body.style.overflow = '';
  }));
}

/* ライトボックス（ギャラリー/ビフォーアフター） */
const lb = document.querySelector('.lightbox');
if (lb) {
  const lbImg = lb.querySelector('img');
  document.querySelectorAll('[data-lightbox]').forEach(el => {
    el.addEventListener('click', (ev) => {
      ev.preventDefault();
      lbImg.src = el.getAttribute('data-lightbox');
      lb.classList.add('open');
    });
  });
  lb.addEventListener('click', () => lb.classList.remove('open'));
}
