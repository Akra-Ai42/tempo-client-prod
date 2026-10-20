// === Tempo Client — Espace Direction ===

const api = async (path, opts = {}) => {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) { window.location.href = '/static/shared/login.html'; return; }
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
};

async function loadMe() {
  const me = await api('/auth/me');
  document.getElementById('user-name').textContent = me.nom_affiche;
}

async function loadDashboard() {
  try {
    const kpi = await api('/dashboard/direction');
    document.getElementById('kpi-total').textContent = kpi.nb_clients_total;
    document.getElementById('kpi-risque-haut').textContent = kpi.nb_clients_risque_haut;
    document.getElementById('kpi-risque-moyen').textContent = kpi.nb_clients_risque_moyen;
    document.getElementById('kpi-churn').textContent = `${(kpi.taux_churn_predit * 100).toFixed(1)}%`;
    document.getElementById('kpi-cout-llm').textContent = `${kpi.cout_llm_mois_courant_usd.toFixed(2)} $`;

    const deriveEl = document.getElementById('kpi-derive');
    const deriveCard = document.getElementById('kpi-derive-card');
    if (kpi.derive_detectee) {
      deriveEl.textContent = 'Détectée';
      deriveCard.classList.add('alert');
    } else {
      deriveEl.textContent = 'OK';
      deriveCard.classList.remove('alert');
    }
  } catch (e) {
    console.error(e);
  }
}

document.getElementById('logout-btn').addEventListener('click', async () => {
  await api('/auth/logout', { method: 'POST' });
  window.location.href = '/static/shared/login.html';
});

loadMe().then(loadDashboard);
