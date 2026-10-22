// === Tempo Client V2 - Espace Direction ===
// Dashboard KPI business + ML Ops avec SVG donut et top 10 cliquable.

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

function renderDriftSection(drift) {
  const statusLabel = drift.drift_detected ? 'DETECTEE' : 'OK';
  const statusColor = drift.drift_detected ? 'var(--danger)' : 'var(--success)';
  const sharePct = (drift.share_drifted * 100).toFixed(0);

  const featuresList = drift.drifted_features && drift.drifted_features.length
    ? drift.drifted_features.map(f => `<span class="drift-feature">${f}</span>`).join('')
    : '<span class="drift-feature-none">Aucune feature derivee</span>';

  const reportLink = drift.report_available
    ? `<a href="/monitoring/drift/report" target="_blank" class="btn-refresh" style="text-decoration:none;display:inline-block">Voir le rapport Evidently</a>`
    : '';

  const recomputeBtn = `<button class="btn-refresh" id="btn-recompute-drift">Verifier maintenant</button>`;

  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Derive des donnees (Evidently)</div>
        <div style="display:flex;gap:8px">${reportLink}${recomputeBtn}</div>
      </div>
      <div class="portfolio-row" style="grid-template-columns:200px 1fr">
        <div class="donut-container" style="justify-content:center">
          <div style="font-size:11px;color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px">Statut</div>
          <div style="font-size:28px;font-weight:600;color:${statusColor};line-height:1">${statusLabel}</div>
          <div style="font-size:11px;color:var(--text-tertiary);margin-top:8px">${drift.nb_features_drifted}/${drift.nb_features_total} features derivees (${sharePct}%)</div>
        </div>
        <div>
          <div style="font-size:10px;color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px">Features derivees</div>
          <div class="drift-features">${featuresList}</div>
          ${drift.computed_at ? `<div style="font-size:11px;color:var(--text-tertiary);margin-top:16px">Dernier calcul : ${new Date(drift.computed_at).toLocaleString('fr-FR')}</div>` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderDonut(pctHigh, pctMedium, pctLow, totalClients) {
  const radius = 48;
  const strokeWidth = 14;
  const circumference = 2 * Math.PI * radius;
  const highLength = (pctHigh / 100) * circumference;
  const mediumLength = (pctMedium / 100) * circumference;
  const lowLength = (pctLow / 100) * circumference;
  const highOffset = 0;
  const mediumOffset = -highLength;
  const lowOffset = -(highLength + mediumLength);

  return `
    <svg width="140" height="140" viewBox="0 0 140 140">
      <g transform="rotate(-90 70 70)">
        <circle cx="70" cy="70" r="${radius}" fill="none" stroke="var(--surface-3)" stroke-width="${strokeWidth}"></circle>
        <circle cx="70" cy="70" r="${radius}" fill="none" stroke="var(--success)" stroke-width="${strokeWidth}"
                stroke-dasharray="${lowLength} ${circumference}" stroke-dashoffset="${lowOffset}"></circle>
        <circle cx="70" cy="70" r="${radius}" fill="none" stroke="var(--highlight)" stroke-width="${strokeWidth}"
                stroke-dasharray="${mediumLength} ${circumference}" stroke-dashoffset="${mediumOffset}"></circle>
        <circle cx="70" cy="70" r="${radius}" fill="none" stroke="var(--danger)" stroke-width="${strokeWidth}"
                stroke-dasharray="${highLength} ${circumference}" stroke-dashoffset="${highOffset}"></circle>
      </g>
      <text x="70" y="68" text-anchor="middle" font-size="22" font-weight="600" fill="var(--text-primary)" font-family="inherit">${totalClients}</text>
      <text x="70" y="86" text-anchor="middle" font-size="10" fill="var(--text-tertiary)" font-family="inherit" style="text-transform:uppercase;letter-spacing:0.08em">Clients</text>
    </svg>
  `;
}

function renderPortfolioSection(portfolio) {
  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Portefeuille clients</div>
      </div>
      <div class="portfolio-row">
        <div class="donut-container">
          ${renderDonut(portfolio.pct_high, portfolio.pct_medium, portfolio.pct_low, portfolio.total_clients)}
          <div class="donut-legend">
            <div class="legend-item"><span class="legend-dot" style="background:var(--danger)"></span>High ${portfolio.pct_high}% (${portfolio.nb_high})</div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--highlight)"></span>Medium ${portfolio.pct_medium}% (${portfolio.nb_medium})</div>
            <div class="legend-item"><span class="legend-dot" style="background:var(--success)"></span>Low ${portfolio.pct_low}% (${portfolio.nb_low})</div>
          </div>
        </div>
        <div class="portfolio-stats">
          <div class="portfolio-stat">
            <div class="label">Score moyen portefeuille</div>
            <div class="value">${portfolio.score_moyen}</div>
          </div>
          <div class="portfolio-stat">
            <div class="label">Taux churn predit</div>
            <div class="value">${formatPct(portfolio.taux_churn_predit)}</div>
          </div>
          <div class="portfolio-stat">
            <div class="label">Clients haute urgence</div>
            <div class="value" style="color:var(--danger)">${portfolio.nb_high}</div>
          </div>
          <div class="portfolio-stat">
            <div class="label">Clients moyenne urgence</div>
            <div class="value" style="color:var(--highlight)">${portfolio.nb_medium}</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderMLOpsSection(ml) {
  const lastCall = ml.last_call_at
    ? new Date(ml.last_call_at).toLocaleString('fr-FR')
    : 'Aucun';
  const hitClass = ml.hit_rate_pct >= 70 ? 'success' : (ml.hit_rate_pct >= 40 ? 'warning' : 'alert');
  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">ML Ops - Sante systeme</div>
      </div>
      <div class="kpi-grid-direction">
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Cout LLM mois courant</div>
          <div class="kpi-value">${formatUsd(ml.cost_llm_mois_courant_usd)}</div>
          <div class="kpi-sub-direction">${ml.nb_appels_mois} appel${ml.nb_appels_mois > 1 ? 's' : ''} ce mois-ci</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Cout LLM 24h</div>
          <div class="kpi-value">${formatUsd(ml.cost_llm_24h_usd)}</div>
          <div class="kpi-sub-direction">${ml.nb_appels_24h} appel${ml.nb_appels_24h > 1 ? 's' : ''} dernieres 24h</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Hit rate cache</div>
          <div class="kpi-value ${hitClass}">${formatPct(ml.hit_rate_pct)}</div>
          <div class="kpi-sub-direction">Objectif cible : 80%</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Latence moyenne LLM</div>
          <div class="kpi-value">${ml.avg_latency_ms}ms</div>
          <div class="kpi-sub-direction">Dernier appel : ${lastCall}</div>
        </div>
      </div>
    </div>
  `;
}

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

async function loadMe() {
  const me = await api('/auth/me');
  document.getElementById('user-name').textContent = me.full_name;
  document.getElementById('user-avatar').textContent = initials(me.full_name);
}

async function loadDashboard() {
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="loading-state">Chargement du dashboard...</div>';

  try {
    const kpi = await api('/dashboard/direction');
    main.innerHTML = `
      <div class="section-direction">
        <div class="section-head">
          <div class="section-title-big">Vue d'ensemble</div>
          <button class="btn-refresh" id="btn-refresh">Actualiser</button>
        </div>
      </div>
      ${renderPortfolioSection(kpi.portfolio)}
      ${renderMLOpsSection(kpi.ml_ops)}
      ${renderDriftSection(kpi.drift)}
      ${renderTopList(kpi.top_clients_risque)}
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
