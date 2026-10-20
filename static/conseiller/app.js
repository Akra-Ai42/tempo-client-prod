// === Tempo Client — Espace Conseiller ===

const api = async (path, opts = {}) => {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) { window.location.href = '/static/shared/login.html'; return; }
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
};

// Charge l'identité du user
async function loadMe() {
  const me = await api('/auth/me');
  document.getElementById('user-name').textContent = `${me.nom_affiche} — ${me.region || 'toutes régions'}`;
}

// Charge la liste des clients du conseiller
async function loadClients() {
  const tbody = document.getElementById('clients-tbody');
  try {
    const clients = await api('/clients/mine');
    tbody.innerHTML = '';
    if (!clients.length) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#8a8a8a">Aucun client à afficher</td></tr>';
      return;
    }
    for (const c of clients) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${c.prenom} ${c.nom}</td>
        <td>${c.region}</td>
        <td>${c.anciennete_mois} mois</td>
        <td>${c.produits_detenus}</td>
        <td>${c.solde_moyen.toFixed(0)} €</td>
        <td>${(c.score_churn * 100).toFixed(0)}%</td>
        <td class="urgence-${c.urgence}">${c.urgence.toUpperCase()}</td>
      `;
      tr.addEventListener('click', () => openClient(c.id, `${c.prenom} ${c.nom}`));
      tbody.appendChild(tr);
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:#9c3b3b">Erreur : ${e.message}</td></tr>`;
  }
}

// Ouvre la fiche d'un client
async function openClient(clientId, displayName) {
  const panel = document.getElementById('client-detail');
  panel.hidden = false;
  document.getElementById('client-detail-name').textContent = displayName;

  const featureList = document.getElementById('feature-list');
  const explBox = document.getElementById('explanation-box');
  const recoList = document.getElementById('reco-list');
  featureList.innerHTML = '<li>Chargement…</li>';
  explBox.textContent = 'Chargement de l\'explication…';
  recoList.innerHTML = '';

  try {
    // Score + top features
    const score = await api(`/score/${clientId}`, { method: 'POST' });
    featureList.innerHTML = '';
    for (const f of score.top_features) {
      const li = document.createElement('li');
      li.innerHTML = `<span>${f.feature}</span><span>${f.direction} ${f.shap_value.toFixed(3)}</span>`;
      featureList.appendChild(li);
    }

    // Explication LLM
    const expl = await api(`/explain/${clientId}`, { method: 'POST' });
    explBox.textContent = expl.explication;

    // Recommandations
    const reco = await api(`/recommend/${clientId}`, { method: 'POST' });
    recoList.innerHTML = '';
    for (const r of reco.recommandations) {
      const div = document.createElement('div');
      div.className = 'reco-item';
      div.innerHTML = `<strong>${r.action}</strong> — ${r.priorite}<br><span style="color:#8a8a8a">${r.justification}</span>`;
      recoList.appendChild(div);
    }
  } catch (e) {
    explBox.textContent = `Erreur : ${e.message}`;
  }
}

// Déconnexion
document.getElementById('logout-btn').addEventListener('click', async () => {
  await api('/auth/logout', { method: 'POST' });
  window.location.href = '/static/shared/login.html';
});

// Démarrage
loadMe().then(loadClients);
