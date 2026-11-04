// === Tempo Client - Espace Direction (upgrade UX) ===
// Dashboard narratif en 3 sections : Contexte / Signaux / Synthese.
// Public cible : profil dev/ops (comprendre ce qui se passe dans le systeme).

const api = async (path, opts = {}) => {
  const res = await fetch(path, { credentials: 'same-origin', ...opts });
  if (res.status === 401) {
    window.location.href = '/static/shared/login.html';
    return;
  }
  if (!res.ok) {
    const err = new Error(`${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
};

const initials = (fullName) => {
  if (!fullName) return '?';
  const parts = fullName.trim().split(/\s+/);
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase();
};

const formatUsd = (n) => `${n.toFixed(6)} USD`;
const formatPct = (n) => `${n.toFixed(1)}%`;
const formatInt = (n) => n.toLocaleString('fr-FR');

// === Mini-courbe en barres (histogramme CSS pur, pas de lib) ===

function renderMiniBars(values, maxBars, colorClass) {
  if (!values || values.length === 0) {
    return '<div class="minibars-empty">Pas de donnees</div>';
  }
  const slice = values.slice(-maxBars);
  const min = Math.min(...slice);
  const max = Math.max(...slice);
  const range = max - min || 1;
  const bars = slice.map((v, i) => {
    const h = 8 + ((v - min) / range) * 42;
    const isLatest = i >= slice.length - 3;
    return `<div class="minibar ${isLatest ? colorClass : 'muted'}" style="height:${h.toFixed(1)}px"></div>`;
  }).join('');
  return `<div class="minibars">${bars}</div>`;
}

// === Section 1 : Ce qui se passe aujourd hui (contexte avec narrative) ===

function narrativeScorings(trends) {
  if (!trends || !trends.points || trends.points.length < 2) {
    return 'Pas assez de donnees pour commenter la tendance.';
  }
  const high = trends.points.map(p => p.nb_high);
  const last = high[high.length - 1];
  const first = high[0];
  const delta = last - first;
  if (Math.abs(delta) < 2) {
    return 'Le portefeuille a risque reste stable sur la fenetre observee.';
  }
  if (delta > 0) {
    return `Le nombre de clients haute urgence a augmente de ${first} a ${last} sur la fenetre. A surveiller.`;
  }
  return `Le nombre de clients haute urgence a diminue de ${first} a ${last} sur la fenetre. Bonne dynamique.`;
}

function narrativeCost(trends) {
  if (!trends || !trends.points || trends.points.length < 2) {
    return 'Pas assez de donnees pour commenter la tendance.';
  }
  const costs = trends.points.map(p => p.cost_llm_mois);
  const last = costs[costs.length - 1];
  const first = costs[0];
  const deltaPct = first > 0 ? ((last - first) / first) * 100 : 0;
  if (Math.abs(deltaPct) < 5) {
    return 'Le cout LLM mois courant progresse dans la norme.';
  }
  if (deltaPct > 20) {
    return `Hausse significative du cout LLM (+${deltaPct.toFixed(0)}% sur la fenetre). A investiguer.`;
  }
  if (deltaPct > 0) {
    return `Hausse moderee du cout LLM (+${deltaPct.toFixed(0)}% sur la fenetre).`;
  }
  return `Baisse du cout LLM (${deltaPct.toFixed(0)}% sur la fenetre).`;
}

function renderContexteSection(kpi, trends) {
  const highSeries = trends && trends.points ? trends.points.map(p => p.nb_high) : [];
  const costSeries = trends && trends.points ? trends.points.map(p => p.cost_llm_mois) : [];

  const lastHigh = kpi.portfolio.nb_high;
  const firstHigh = highSeries.length ? highSeries[0] : lastHigh;
  const highDelta = lastHigh - firstHigh;
  const highDeltaLabel = highDelta === 0
    ? 'stable'
    : (highDelta > 0 ? `+${highDelta} vs debut fenetre` : `${highDelta} vs debut fenetre`);
  const highDeltaColor = highDelta > 0 ? 'var(--danger)' : (highDelta < 0 ? 'var(--success)' : 'var(--text-tertiary)');

  const lastCost = kpi.ml_ops.cost_llm_mois_courant_usd;
  const firstCost = costSeries.length ? costSeries[0] : lastCost;
  const costDeltaPct = firstCost > 0 ? ((lastCost - firstCost) / firstCost) * 100 : 0;
  const costDeltaLabel = Math.abs(costDeltaPct) < 1
    ? 'stable'
    : `${costDeltaPct > 0 ? '+' : ''}${costDeltaPct.toFixed(0)}% vs debut fenetre`;
  const costDeltaColor = costDeltaPct > 20 ? 'var(--danger)' : (costDeltaPct > 0 ? 'var(--highlight)' : 'var(--success)');

  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Ce qui se passe aujourd hui</div>
      </div>

      <div class="narrative-row">
        <div class="narrative-card">
          <div class="narrative-head">
            <div class="narrative-title">Clients haute urgence</div>
            <div class="narrative-delta" style="color:${highDeltaColor}">${highDeltaLabel}</div>
          </div>
          <div class="narrative-value">${formatInt(lastHigh)}</div>
          ${renderMiniBars(highSeries, 12, 'accent')}
          <div class="narrative-text">${narrativeScorings(trends)}</div>
        </div>

        <div class="narrative-card">
          <div class="narrative-head">
            <div class="narrative-title">Cout LLM mois courant</div>
            <div class="narrative-delta" style="color:${costDeltaColor}">${costDeltaLabel}</div>
          </div>
          <div class="narrative-value">${formatUsd(lastCost)}</div>
          ${renderMiniBars(costSeries, 12, 'danger')}
          <div class="narrative-text">${narrativeCost(trends)}</div>
        </div>
      </div>
    </div>
  `;
}

// === Section 2 : Signaux techniques (milieu) ===

function renderSignauxSection(kpi) {
  const latencyMs = kpi.ml_ops.avg_latency_ms;
  const latencyColor = latencyMs > 3000 ? 'var(--danger)' : (latencyMs > 1500 ? 'var(--highlight)' : 'var(--success)');
  const hitPct = kpi.ml_ops.hit_rate_pct;
  const hitColor = hitPct >= 70 ? 'var(--success)' : (hitPct >= 40 ? 'var(--highlight)' : 'var(--danger)');

  const drift = kpi.drift;
  const driftFeatures = drift.drifted_features && drift.drifted_features.length
    ? drift.drifted_features.map(f => `<span class="drift-feature">${f}</span>`).join('')
    : '<span class="drift-feature-none">Aucune feature derivee</span>';
  const driftShare = drift.nb_features_total > 0
    ? `${drift.nb_features_drifted}/${drift.nb_features_total} features (${(drift.share_drifted * 100).toFixed(0)}%)`
    : 'n/a';

  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Signaux techniques</div>
      </div>

      <div class="signaux-grid">
        <div class="signal-small-card">
          <div class="signal-label">Latence moyenne LLM</div>
          <div class="signal-value" style="color:${latencyColor}">${latencyMs}<span class="signal-unit">ms</span></div>
        </div>
        <div class="signal-small-card">
          <div class="signal-label">Hit rate cache</div>
          <div class="signal-value" style="color:${hitColor}">${hitPct.toFixed(0)}<span class="signal-unit">%</span></div>
        </div>
      </div>

      <div class="signal-wide-card">
        <div class="signal-wide-head">
          <div class="signal-label">Derive des donnees (Evidently)</div>
          <div class="signal-wide-meta">${driftShare}</div>
        </div>
        <div class="drift-features">${driftFeatures}</div>
        ${drift.computed_at ? `<div class="signal-wide-footer">Dernier calcul : ${new Date(drift.computed_at).toLocaleString('fr-FR')}</div>` : ''}
      </div>
    </div>
  `;
}

// === Section 3 : Synthese chiffree (KPI en bas) ===

function renderSyntheseSection(kpi) {
  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Synthese chiffree</div>
      </div>
      <div class="kpi-grid-direction">
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Portefeuille total</div>
          <div class="kpi-value">${formatInt(kpi.portfolio.total_clients)}</div>
          <div class="kpi-sub-direction">score moyen ${kpi.portfolio.score_moyen}</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Clients haute urgence</div>
          <div class="kpi-value alert">${formatInt(kpi.portfolio.nb_high)}</div>
          <div class="kpi-sub-direction">${kpi.portfolio.pct_high}% du portefeuille</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Cout LLM 24h</div>
          <div class="kpi-value ${kpi.ml_ops.cost_llm_24h_usd > kpi.ml_ops.cost_llm_mois_courant_usd / 30 * 2 ? 'alert' : ''}">${formatUsd(kpi.ml_ops.cost_llm_24h_usd)}</div>
          <div class="kpi-sub-direction">${kpi.ml_ops.nb_appels_24h} appels</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Taux churn predit</div>
          <div class="kpi-value warning">${formatPct(kpi.portfolio.taux_churn_predit)}</div>
          <div class="kpi-sub-direction">sur l ensemble du portefeuille</div>
        </div>
      </div>
    </div>
  `;
}

// === Top clients (gardee mais placee entre signaux et synthese) ===

function renderTopList(topClients) {
  if (!topClients.length) {
    return `
      <div class="section-direction">
        <div class="section-head">
          <div class="section-title-big">Top 10 clients a risque</div>
        </div>
        <div class="top-list"><div class="loading-state">Aucun client a afficher.</div></div>
      </div>
    `;
  }

  const maxScore = Math.max(...topClients.map(c => c.score_churn));

  const rows = topClients.map((c, idx) => {
    const barWidth = (c.score_churn / maxScore) * 100;
    const scorePct = (c.score_churn * 100).toFixed(0);
    return `
      <div class="top-row" data-id="${c.id}" title="Ouvrir la fiche conseiller du client ${c.id}">
        <div class="rank">${idx + 1}</div>
        <div>
          <span class="top-name">${c.prenom} ${c.nom}</span>
          <span class="top-region">${c.region}</span>
        </div>
        <div class="top-score urgence-${c.urgence}">${scorePct}%</div>
        <div class="bar-container">
          <div class="bar-fill ${c.urgence}" style="width:${barWidth}%"></div>
        </div>
        <div class="arrow">&gt;</div>
      </div>
    `;
  }).join('');

  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Top 10 clients a risque (toutes regions)</div>
      </div>
      <div class="top-list">${rows}</div>
    </div>
  `;
}

// === Load & render ===

async function loadMe() {
  const me = await api('/auth/me');
  document.getElementById('user-name').textContent = me.full_name;
  document.getElementById('user-avatar').textContent = initials(me.full_name);
}

async function loadDashboard() {
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="loading-state">Chargement du dashboard...</div>';

  try {
    const [kpi, trends] = await Promise.all([
      api('/dashboard/direction'),
      api('/dashboard/direction/trends?hours=24').catch(() => ({ hours: 24, nb_points: 0, points: [] })),
    ]);

    main.innerHTML = `
      <div class="section-direction" style="margin-bottom:20px">
        <div class="section-head">
          <div class="section-title-big">Vue d ensemble</div>
          <button class="btn-refresh" id="btn-refresh">Actualiser</button>
        </div>
      </div>
      ${renderContexteSection(kpi, trends)}
      ${renderSignauxSection(kpi)}
      ${renderTopList(kpi.top_clients_risque)}
      ${renderSyntheseSection(kpi)}
    `;

    document.getElementById('btn-refresh').addEventListener('click', loadDashboard);

    main.querySelectorAll('.top-row').forEach(row => {
      row.addEventListener('click', () => {
        window.open(`/static/conseiller/index.html`, '_blank');
      });
    });
  } catch (e) {
    main.innerHTML = `<div class="loading-state" style="color:var(--danger)">Erreur : ${e.message}</div>`;
  }
}

document.getElementById('logout-btn').addEventListener('click', async () => {
  try { await api('/auth/logout', { method: 'POST' }); } catch (e) {}
  window.location.href = '/static/shared/login.html';
});

loadMe().then(loadDashboard).catch(e => {
  console.error('Erreur chargement initial :', e);
  document.getElementById('main-content').innerHTML = `
    <div class="loading-state" style="color:var(--danger)">Erreur : ${e.message}</div>
  `;
});
