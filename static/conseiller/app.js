// === Tempo Client V2 - Espace Conseiller ===
// UX premium : sidebar + hero + KPI + chat + checklist

const api = async (path, opts = {}) => {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) {
    window.location.href = '/static/shared/login.html';
    return;
  }
  if (!res.ok) {
    const err = new Error(`${res.status}`);
    err.status = res.status;
    err.body = await res.text();
    throw err;
  }
  return res.json();
};

// === Etat global ===
const state = {
  user: null,
  clients: [],
  filteredClients: [],
  currentUrgence: 'all',
  currentSearch: '',
  currentClientId: null,
  doneRecos: JSON.parse(localStorage.getItem('tempo_done_recos') || '{}'),
};

// === Utilitaires ===

const initials = (fullName) => {
  if (!fullName) return '?';
  const parts = fullName.trim().split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
};

const formatFeatureName = (name) => ({
  nb_interactions_90j: 'Interactions sur 90j',
  derniere_interaction_jours: 'Derniere interaction (jours)',
  solde_moyen: 'Solde moyen',
  produits_detenus: 'Produits detenus',
  anciennete_mois: 'Anciennete (mois)',
  age_client: 'Age du client',
  canal_prefere: 'Canal prefere',
}[name] || name);

const formatCurrency = (n) => new Intl.NumberFormat('fr-FR', {
  style: 'currency', currency: 'EUR', maximumFractionDigits: 0,
}).format(n);

// === Chargement initial ===

async function loadMe() {
  const me = await api('/auth/me');
  state.user = me;
  const region = me.region ? me.region : 'toutes regions';
  document.getElementById('user-name').textContent = `${me.full_name} - ${region}`;
  document.getElementById('user-avatar').textContent = initials(me.full_name);
}

async function loadClients() {
  const clients = await api('/clients/mine');
  state.clients = clients;
  applyFiltersAndRender();
}

// === Sidebar : filtres + rendu ===

function applyFiltersAndRender() {
  let list = state.clients;

  if (state.currentUrgence !== 'all') {
    list = list.filter(c => c.urgence === state.currentUrgence);
  }

  if (state.currentSearch) {
    const q = state.currentSearch.toLowerCase();
    list = list.filter(c =>
      `${c.prenom} ${c.nom}`.toLowerCase().includes(q)
    );
  }

  state.filteredClients = list;
  renderSidebar();
}

function renderSidebar() {
  const container = document.getElementById('sidebar-list');
  const footer = document.getElementById('sidebar-footer');

  if (!state.filteredClients.length) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:#8a8a8a;font-size:12px">Aucun client ne correspond</div>';
    footer.textContent = `0 / ${state.clients.length} clients`;
    return;
  }

  container.innerHTML = '';
  for (const c of state.filteredClients) {
    const item = document.createElement('div');
    item.className = 'sidebar-item' + (c.id === state.currentClientId ? ' active' : '');
    const scorePct = (c.score_churn * 100).toFixed(0);
    item.innerHTML = `
      <div class="urgence-dot ${c.urgence}"></div>
      <div class="client-info">
        <div class="client-name">${c.prenom} ${c.nom}</div>
        <div class="client-meta">${c.region} · ${c.anciennete_mois} mois</div>
      </div>
      <div class="client-score">${scorePct}%</div>
    `;
    item.addEventListener('click', () => openClient(c));
    container.appendChild(item);
  }

  footer.textContent = `${state.filteredClients.length} / ${state.clients.length} clients`;
}

// === Fiche client ===

function renderGauge(scorePct, urgence) {
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - scorePct / 100);
  return `
    <div class="gauge ${urgence}">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle class="gauge-bg" cx="36" cy="36" r="${radius}"></circle>
        <circle class="gauge-fill" cx="36" cy="36" r="${radius}"
                stroke-dasharray="${circumference}"
                stroke-dashoffset="${offset}"></circle>
      </svg>
      <div class="gauge-text">
        <div class="gauge-value">${scorePct}%</div>
        <div class="gauge-label">${urgence}</div>
      </div>
    </div>
  `;
}

function renderHero(client) {
  const scorePct = Math.round(client.score_churn * 100);
  return `
    <div class="hero-v2">
      <div class="hero-info">
        <div class="hero-name">${client.prenom} ${client.nom}</div>
        <div class="hero-meta">
          ${client.age_client} ans · ${client.region} ·
          ${Math.round(client.anciennete_mois / 12)} ans de relation ·
          Client #${client.id}
        </div>
      </div>
      ${renderGauge(scorePct, client.urgence)}
    </div>
  `;
}

function renderKPICards(client) {
  return `
    <div class="kpi-row">
      <div class="kpi-card-v2">
        <div class="kpi-head">
          <svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-6 8-6s8 2 8 6"/></svg>
          <div class="kpi-head-label">Profil</div>
        </div>
        <div class="kpi-value">${client.age_client}</div>
        <div class="kpi-sub-v2">ans · anciennete ${client.anciennete_mois} mois</div>
      </div>

      <div class="kpi-card-v2">
        <div class="kpi-head">
          <svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 12c0-5 4-9 9-9s9 4 9 9c0 2-1 4-2 5l2 4-4-2c-1 1-3 2-5 2-5 0-9-4-9-9z"/></svg>
          <div class="kpi-head-label">Activite</div>
        </div>
        <div class="kpi-value">${client.nb_interactions_90j}</div>
        <div class="kpi-sub-v2">interactions · derniere il y a ${client.derniere_interaction_jours}j</div>
      </div>

      <div class="kpi-card-v2">
        <div class="kpi-head">
          <svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/></svg>
          <div class="kpi-head-label">Finance</div>
        </div>
        <div class="kpi-value">${formatCurrency(client.solde_moyen)}</div>
        <div class="kpi-sub-v2">solde moyen · ${client.produits_detenus} produit${client.produits_detenus > 1 ? 's' : ''}</div>
      </div>

      <div class="kpi-card-v2">
        <div class="kpi-head">
          <svg class="kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2l10 20H2L12 2z"/><path d="M12 10v5" stroke-linecap="round"/><circle cx="12" cy="18" r="1" fill="currentColor"/></svg>
          <div class="kpi-head-label">Risque</div>
        </div>
        <div class="kpi-value">${Math.round(client.score_churn * 100)}<span style="font-size:16px;color:var(--text-tertiary)">%</span></div>
        <div class="kpi-sub-v2 urgence-${client.urgence}" style="font-weight:600">${client.urgence.toUpperCase()}</div>
      </div>
    </div>
  `;
}

async function loadAndRenderSHAP(clientId, container) {
  container.innerHTML = `<div class="section-v2">
    <div class="section-title">Top facteurs explicatifs</div>
    <div class="shap-list"><div style="padding:16px;text-align:center;color:#8a8a8a;font-size:12px">Chargement...</div></div>
  </div>`;

  try {
    const score = await api(`/score/${clientId}`, { method: 'POST' });
    const rows = score.top_features.map(f => {
      const up = f.direction === '+';
      const arrow = up ? '↑' : '↓';
      return `
        <div class="shap-row">
          <div class="shap-label">${formatFeatureName(f.feature)}</div>
          <div class="shap-value">${f.value}</div>
          <div class="shap-contrib ${up ? 'up' : 'down'}">${arrow} ${Math.abs(f.shap_value).toFixed(2)}</div>
        </div>
      `;
    }).join('');
    container.innerHTML = `<div class="section-v2">
      <div class="section-title">Top facteurs explicatifs</div>
      <div class="shap-list">${rows}</div>
    </div>`;
  } catch (e) {
    container.innerHTML = `<div class="section-v2">
      <div class="section-title">Top facteurs explicatifs</div>
      <div class="shap-list"><div style="padding:16px;color:#9c3b3b;font-size:12px">Erreur : ${e.message}</div></div>
    </div>`;
  }
}

async function loadAndRenderExplain(clientId, container) {
  container.innerHTML = `
    <div class="section-v2">
      <div class="section-title">Analyse contextuelle</div>
      <div class="chat-v2">
        <div class="chat-header">
          <div class="dot"></div>
          <div class="title">Tempo Analyst</div>
        </div>
        <div class="chat-body">
          <div class="bubble loading">Analyse en cours...</div>
        </div>
        <div class="chat-input">
          <input type="text" placeholder="Posez une question au modele..." disabled>
          <span class="send-hint">bientot</span>
        </div>
      </div>
    </div>
  `;

  try {
    const expl = await api(`/explain/${clientId}`, { method: 'POST' });
    const cacheClass = expl.from_cache ? 'cache-hit' : 'cache-miss';
    const cacheLabel = expl.from_cache ? 'Cache HIT' : 'Cache MISS';
    const latency = expl.latency_ms != null ? `${expl.latency_ms}ms` : '-';
    const cost = expl.cost_usd != null ? `${expl.cost_usd.toFixed(6)} USD` : '-';
    const body = container.querySelector('.chat-body');
    body.innerHTML = `
      <div class="bubble">${expl.explication}</div>
      <div class="bubble-meta">
        <span class="${cacheClass}">${cacheLabel}</span>
        <span>${latency}</span>
        <span>${cost}</span>
      </div>
    `;
  } catch (e) {
    const body = container.querySelector('.chat-body');
    body.innerHTML = `<div class="bubble" style="color:#9c3b3b">Erreur : ${e.message}</div>`;
  }
}

async function loadAndRenderRecos(clientId, container) {
  container.innerHTML = `
    <div class="section-v2">
      <div class="section-title">Actions recommandees</div>
      <div class="reco-list-v2"><div style="padding:16px;text-align:center;color:#8a8a8a;font-size:12px">Chargement...</div></div>
    </div>
  `;

  try {
    const reco = await api(`/recommend/${clientId}`, { method: 'POST' });
    const listContainer = container.querySelector('.reco-list-v2');
    if (!reco.recommandations.length) {
      listContainer.innerHTML = `<div style="padding:16px;text-align:center;color:#8a8a8a;font-size:12px;font-style:italic">Aucune action proactive requise.</div>`;
      return;
    }
    const doneForClient = state.doneRecos[clientId] || [];
    listContainer.innerHTML = reco.recommandations.map((r, idx) => {
      const isDone = doneForClient.includes(idx);
      return `
        <div class="reco-row ${isDone ? 'done' : ''}" data-idx="${idx}">
          <div class="reco-check ${isDone ? 'checked' : ''}"></div>
          <div class="reco-content">
            <div class="reco-head-row">
              <div class="priority-dot ${r.priorite}"></div>
              <div class="reco-action">${r.action}</div>
            </div>
            <div class="reco-just">${r.justification}</div>
          </div>
        </div>
      `;
    }).join('');

    // Attacher les handlers de checkbox
    listContainer.querySelectorAll('.reco-row').forEach(row => {
      row.addEventListener('click', () => toggleReco(clientId, parseInt(row.dataset.idx), row));
    });
  } catch (e) {
    const listContainer = container.querySelector('.reco-list-v2');
    listContainer.innerHTML = `<div style="padding:16px;color:#9c3b3b;font-size:12px">Erreur : ${e.message}</div>`;
  }
}

function toggleReco(clientId, idx, row) {
  const key = String(clientId);
  if (!state.doneRecos[key]) state.doneRecos[key] = [];
  const list = state.doneRecos[key];
  const pos = list.indexOf(idx);
  if (pos === -1) {
    list.push(idx);
    row.classList.add('done');
    row.querySelector('.reco-check').classList.add('checked');
  } else {
    list.splice(pos, 1);
    row.classList.remove('done');
    row.querySelector('.reco-check').classList.remove('checked');
  }
  localStorage.setItem('tempo_done_recos', JSON.stringify(state.doneRecos));
}

async function openClient(client) {
  state.currentClientId = client.id;
  renderSidebar();  // highlight actif

  const main = document.getElementById('main-content');
  main.innerHTML = `
    ${renderHero(client)}
    ${renderKPICards(client)}
    <div id="section-shap"></div>
    <div id="section-explain"></div>
    <div id="section-recos"></div>
  `;

  // Charger les 3 sections en parallele (chacune met a jour son conteneur)
  loadAndRenderSHAP(client.id, document.getElementById('section-shap'));
  loadAndRenderExplain(client.id, document.getElementById('section-explain'));
  loadAndRenderRecos(client.id, document.getElementById('section-recos'));
}

// === Event listeners ===

document.getElementById('search-input').addEventListener('input', (e) => {
  state.currentSearch = e.target.value;
  applyFiltersAndRender();
});

document.getElementById('urgence-pills').addEventListener('click', (e) => {
  if (!e.target.classList.contains('pill')) return;
  document.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  e.target.classList.add('active');
  state.currentUrgence = e.target.dataset.urgence;
  applyFiltersAndRender();
});

document.getElementById('logout-btn').addEventListener('click', async () => {
  try { await api('/auth/logout', { method: 'POST' }); } catch (e) {}
  window.location.href = '/static/shared/login.html';
});

// === Boot ===

loadMe()
  .then(loadClients)
  .catch(err => {
    console.error('Erreur chargement initial :', err);
    document.getElementById('main-content').innerHTML = `
      <div class="empty-state">
        <div class="icon">!</div>
        <div>Erreur de chargement : ${err.message}</div>
      </div>
    `;
  });
