// === Tempo Client . Espace Conseiller (dark marine + IBM Plex + encarts) ===

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

const state = {
  user: null,
  clients: [],
  filteredClients: [],
  currentUrgence: 'all',
  currentSearch: '',
  currentClientId: null,
  doneRecos: JSON.parse(localStorage.getItem('tempo_done_recos') || '{}'),
};

const initials = (fullName) => {
  if (!fullName) return '?';
  const parts = fullName.trim().split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
};

const formatCurrency = (n) => new Intl.NumberFormat('fr-FR', {
  style: 'currency', currency: 'EUR', maximumFractionDigits: 0,
}).format(n);

const nowHHMM = () => {
  const d = new Date();
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

async function loadMe() {
  const me = await api('/auth/me');
  state.user = me;
  const region = me.region ? me.region : 'toutes regions';
  document.getElementById('user-name').textContent = `${me.full_name} . ${region}`;
  document.getElementById('user-avatar').textContent = initials(me.full_name);
}

async function loadClients() {
  const clients = await api('/clients/mine');
  state.clients = clients;
  applyFiltersAndRender();
}

function applyFiltersAndRender() {
  let list = state.clients;
  if (state.currentUrgence !== 'all') list = list.filter(c => c.urgence === state.currentUrgence);
  if (state.currentSearch) {
    const q = state.currentSearch.toLowerCase();
    list = list.filter(c => `${c.prenom} ${c.nom}`.toLowerCase().includes(q));
  }
  state.filteredClients = list;
  renderSidebar();
}

function renderSidebar() {
  const container = document.getElementById('sidebar-list');
  const footer = document.getElementById('sidebar-footer');

  if (!state.filteredClients.length) {
    container.innerHTML = '<div style="padding:20px;text-align:center;color:#7a869c;font-size:12px">Aucun client ne correspond</div>';
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
        <div class="client-meta">${c.region} . ${c.anciennete_mois} mois</div>
      </div>
      <div class="client-score">${scorePct}%</div>
    `;
    item.addEventListener('click', () => openClient(c));
    container.appendChild(item);
  }
  footer.textContent = `${state.filteredClients.length} / ${state.clients.length} clients`;
}

// === Score header remplace l ancien gauge + hero ===

function renderHeader(client) {
  const scorePct = Math.round(client.score_churn * 100);
  const urg = client.urgence;
  return `
    <div class="hero-v2">
      <div class="hero-info">
        <div class="hero-name">${client.prenom} ${client.nom}</div>
        <div class="hero-meta">
          Client #${client.id} . ${client.age_client} ans . ${client.region} . ${Math.round(client.anciennete_mois / 12)} ans de relation
        </div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
        <div style="font-size:10px;color:var(--text-tertiary);letter-spacing:0.08em;text-transform:uppercase;font-weight:600">Score de risque churn</div>
        <div class="score-block">
          <div class="score-value ${urg}">${scorePct}%</div>
          <div class="score-tag ${urg}">${urg === 'high' ? 'HAUTE URGENCE' : (urg === 'medium' ? 'URGENCE MOY.' : 'URGENCE FAIBLE')}</div>
        </div>
        <div class="mono" style="font-size:10px;color:var(--text-tertiary);margin-top:2px">XGBoost v1.2 . Calcule ${nowHHMM()}</div>
      </div>
    </div>
  `;
}

function renderKPICards(client) {
  return `
    <div class="kpi-row">
      <div class="kpi-card-v2">
        <div class="kpi-head"><div class="kpi-head-label">Profil</div></div>
        <div class="kpi-value">${client.age_client}</div>
        <div class="kpi-sub-v2">ans . anciennete ${client.anciennete_mois} mois</div>
      </div>
      <div class="kpi-card-v2">
        <div class="kpi-head"><div class="kpi-head-label">Activite</div></div>
        <div class="kpi-value">${client.nb_interactions_90j}</div>
        <div class="kpi-sub-v2">interactions . derniere il y a ${client.derniere_interaction_jours}j</div>
      </div>
      <div class="kpi-card-v2">
        <div class="kpi-head"><div class="kpi-head-label">Finance</div></div>
        <div class="kpi-value">${formatCurrency(client.solde_moyen)}</div>
        <div class="kpi-sub-v2">solde moyen . ${client.produits_detenus} produit${client.produits_detenus > 1 ? 's' : ''}</div>
      </div>
      <div class="kpi-card-v2">
        <div class="kpi-head"><div class="kpi-head-label">Risque</div></div>
        <div class="kpi-value">${Math.round(client.score_churn * 100)}<span style="font-size:12px;color:var(--text-tertiary)">%</span></div>
        <div class="kpi-sub-v2 urgence-${client.urgence}" style="font-weight:600">${client.urgence.toUpperCase()}</div>
      </div>
    </div>
  `;
}

// === Les 3 zones avec encart droite ===

const ZONE_NOTES = {
  shap: {
    num: 1,
    title: "Derive silencieuse des recommandations",
    ex: "ex : la meme recommandation qui revient pour tous les clients, sans rapport avec leur profil reel.",
  },
  explain: {
    num: 2,
    title: "Facture LLM qui s'emballe",
    ex: "ex : cout qui triple sans raison, hit rate cache qui chute de 80% a 20% en une heure.",
  },
  recos: {
    num: 3,
    title: "Cascade de valeurs manquantes",
    ex: "ex : une feature NULL qui propage l'erreur jusqu'a l'affichage conseiller.",
  },
};

function renderZoneNote(key) {
  const z = ZONE_NOTES[key];
  return `
    <aside class="zone-note">
      <div class="zone-note-head">Zone pedagogique ${z.num}</div>
      <div class="zone-note-title">${z.title}</div>
      <div class="zone-note-ex">${z.ex}</div>
    </aside>
  `;
}

async function loadAndRenderSHAP(clientId, container) {
  container.innerHTML = `
    <div class="section-v2">
      <div class="section-title">Ce qui pousse ce client vers la sortie</div>
      <div class="facteurs-metier-list"><div style="padding:16px;text-align:center;color:var(--text-tertiary);font-size:12px">Analyse en cours...</div></div>
    </div>
  `;

  try {
    const expl = await api(`/explain-metier/${clientId}`, { method: 'POST' });
    if (!expl.facteurs || expl.facteurs.length === 0) {
      container.querySelector('.facteurs-metier-list').innerHTML = `<div style="padding:16px;text-align:center;color:var(--text-tertiary);font-size:12px;font-style:italic">Aucun facteur significatif identifie.</div>`;
      return;
    }
    const items = expl.facteurs.map(f => {
      const senskls = f.sens === 'positif' ? 'facteur-negatif' : 'facteur-positif';
      return `
        <div class="facteur-metier ${senskls}">
          <div>
            <div class="facteur-phrase">${f.phrase}</div>
            <div class="facteur-justification">${f.justification}</div>
          </div>
          <div class="facteur-poids">${f.poids}%</div>
        </div>
      `;
    }).join('');
    container.querySelector('.facteurs-metier-list').innerHTML = items;
  } catch (e) {
    container.querySelector('.facteurs-metier-list').innerHTML = `<div style="padding:16px;color:var(--danger);font-size:12px">Erreur : ${e.message}</div>`;
  }
}

async function loadAndRenderExplain(clientId, container) {
  container.innerHTML = `
    <div class="section-v2">
      <div class="section-title">Analyse contextuelle . Tempo Analyst</div>
      <div class="chat-v2">
        <div class="chat-body">
          <div class="bubble loading">Analyse en cours...</div>
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
        <span style="color:var(--border-regular)">|</span>
        <span>${latency}</span>
        <span style="color:var(--border-regular)">|</span>
        <span>${cost}</span>
      </div>
    `;
  } catch (e) {
    container.querySelector('.chat-body').innerHTML = `<div class="bubble" style="color:var(--danger)">Erreur : ${e.message}</div>`;
  }
}

async function loadAndRenderRecos(clientId, container) {
  container.innerHTML = `
    <div class="section-v2">
      <div class="section-title">Actions recommandees</div>
      <div class="reco-list-v2"><div style="padding:16px;text-align:center;color:var(--text-tertiary);font-size:12px">Chargement...</div></div>
    </div>
  `;

  try {
    const reco = await api(`/recommend/${clientId}`, { method: 'POST' });
    const listContainer = container.querySelector('.reco-list-v2');
    if (!reco.recommandations.length) {
      listContainer.innerHTML = `<div style="padding:16px;text-align:center;color:var(--text-tertiary);font-size:12px;font-style:italic">Aucune action proactive requise.</div>`;
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
              <div class="reco-action">${r.action}</div>
              <div class="priority-dot ${r.priorite}"></div>
            </div>
            <div class="reco-just">${r.justification}</div>
          </div>
        </div>
      `;
    }).join('');

    listContainer.querySelectorAll('.reco-row').forEach(row => {
      row.addEventListener('click', () => toggleReco(clientId, parseInt(row.dataset.idx), row));
    });
  } catch (e) {
    container.querySelector('.reco-list-v2').innerHTML = `<div style="padding:16px;color:var(--danger);font-size:12px">Erreur : ${e.message}</div>`;
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
  renderSidebar();

  const main = document.getElementById('main-content');
  main.innerHTML = `
    ${renderHeader(client)}
    ${renderKPICards(client)}

    <div class="section-with-note">
      <div id="section-shap"></div>
      ${renderZoneNote('shap')}
    </div>

    <div class="section-with-note">
      <div id="section-explain"></div>
      ${renderZoneNote('explain')}
    </div>

    <div class="section-with-note">
      <div id="section-recos"></div>
      ${renderZoneNote('recos')}
    </div>
  `;

  loadAndRenderSHAP(client.id, document.getElementById('section-shap'));
  loadAndRenderExplain(client.id, document.getElementById('section-explain'));
  loadAndRenderRecos(client.id, document.getElementById('section-recos'));
}

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
