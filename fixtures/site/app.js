// Minimal hash router and storage helpers shared by every page.
(function () {
  if (new URLSearchParams(location.search).has('reset')) {
    Object.keys(localStorage).filter(k => k.startsWith('cedar-')).forEach(k => localStorage.removeItem(k));
    history.replaceState(null, '', location.pathname);
  }

  const listeners = {};
  window.onView = (name, fn) => { (listeners[name] = listeners[name] || []).push(fn); };
  window.go = name => { location.hash = '#' + name; };
  window.store = {
    get: (key, fallback) => {
      try { const v = localStorage.getItem('cedar-' + key); return v === null ? fallback : JSON.parse(v); }
      catch (e) { return fallback; }
    },
    set: (key, value) => localStorage.setItem('cedar-' + key, JSON.stringify(value)),
  };

  function show() {
    const views = [...document.querySelectorAll('[data-view]')];
    const wanted = location.hash.slice(1);
    const main = document.querySelector('main');
    const current = views.find(v => v.dataset.view === wanted) || views.find(v => main.contains(v));
    views.forEach(v => { v.hidden = v !== current; });
    main.hidden = !main.contains(current);
    const header = document.querySelector('header');
    if (header) header.hidden = current.dataset.chrome === 'none';
    (listeners[current.dataset.view] || []).forEach(fn => fn());
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', show);
  document.addEventListener('DOMContentLoaded', show);
})();
