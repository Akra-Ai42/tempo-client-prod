// === Tempo Client — Logique de login commune ===

const form = document.getElementById('login-form');
const errorEl = document.getElementById('login-error');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.hidden = true;

  const data = new FormData(form);
  const payload = {
    username: data.get('username'),
    password: data.get('password'),
  };

  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      credentials: 'same-origin',
    });

    if (!res.ok) {
      const err = await res.json();
      errorEl.textContent = err.detail || 'Erreur de connexion';
      errorEl.hidden = false;
      return;
    }

    const info = await res.json();
    // Redirige vers la bonne interface selon le rôle
    if (info.role === 'direction') {
      window.location.href = '/static/direction/index.html';
    } else {
      window.location.href = '/static/conseiller/index.html';
    }
  } catch (err) {
    errorEl.textContent = 'Erreur réseau';
    errorEl.hidden = false;
  }
});
