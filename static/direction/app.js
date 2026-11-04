// === Tempo Client . Espace Direction (dark marine + courbes SVG + Evidently) ===

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

// === Mini line chart SVG (une courbe continue avec aire translucide) ===

function renderLineChart(values, width, height, colorHex) {
  if (!values || values.length < 2) {
    return `<div style="font-size:11px;color:var(--text-tertiary);padding:8px">Pas assez de donnees</div>`;
  }
  const padding = 4;
  const w = width - padding * 2;
  const h = height - padding * 2;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const points = values.map((v, i) => {
    const x = padding + (i / (values.length - 1)) * w;
    const y = padding + h - ((v - min) / range) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const areaPoints = `${padding},${padding + h} ${points} ${padding + w},${padding + h}`;
  return `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" style="display:block">
      <polygon points="${areaPoints}" fill="${colorHex}" opacity="0.15"></polygon>
      <polyline points="${points}" fill="none" stroke="${colorHex}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"></polyline>
    </svg>
  `;
}

// === Narratives (texte court sous chaque courbe) ===

function narrativeHigh(trends) {
  if (!trends || !trends.points || trends.points.length < 2) return 'Pas assez de donnees.';
  const high = trends.points.map(p => p.nb_high);
  const last = high[high.length - 1];
  const first = high[0];
  const delta = last - first;
  if (Math.abs(delta) < 2) return 'Portefeuille a risque stable sur la fenetre observee.';
  if (delta > 0) return `${delta > 0 ? '+' : ''}${delta} clients passes en haute urgence sur la fenetre.`;
  return `${delta} clients sortis de haute urgence sur la fenetre.`;
}

function narrativeCost(trends) {
  if (!trends || !trends.points || trends.points.length < 2) return 'Pas assez de donnees.';
  const costs = trends.points.map(p => p.cost_llm_mois);
  const last = costs[costs.length - 1];
  const first = costs[0];
  const deltaPct = first > 0 ? ((last - first) / first) * 100 : 0;
  if (Math.abs(deltaPct) < 5) return 'Cout LLM mois courant dans la norme.';
  if (deltaPct > 20) return `Hausse marquee du cout LLM (+${deltaPct.toFixed(0)}% sur la fenetre). A investiguer.`;
  if (deltaPct > 0) return `Hausse moderee du cout LLM (+${deltaPct.toFixed(0)}% sur la fenetre).`;
  return `Baisse du cout LLM (${deltaPct.toFixed(0)}% sur la fenetre).`;
}

function narrativeHitRate(trends) {
  if (!trends || !trends.points || trends.points.length < 2) return 'Pas assez de donnees.';
  const hits = trends.points.map(p => p.hit_rate_pct);
  const last = hits[hits.length - 1];
  const first = hits[0];
  const delta = last - first;
  if (Math.abs(delta) < 5) return 'Hit rate stable.';
  if (delta > 0) return `Amelioration du hit rate (+${delta.toFixed(0)} points).`;
  return `Degradation du hit rate (${delta.toFixed(0)} points). A investiguer cote cache.`;
}

// === Section 1 : Ce qui se passe aujourd hui (3 courbes avec narrative) ===

function renderContexteSection(kpi, trends) {
  const costSeries = trends && trends.points ? trends.points.map(p => p.cost_llm_mois) : [];
  const hitSeries = trends && trends.points ? trends.points.map(p => p.hit_rate_pct) : [];
  const highSeries = trends && trends.points ? trends.points.map(p => p.nb_high) : [];

  const lastCost = kpi.ml_ops.cost_llm_mois_courant_usd;
  const lastHit = kpi.ml_ops.hit_rate_pct;
  const lastHigh = kpi.portfolio.nb_high;

  const costDelta = costSeries.length ? ((lastCost - costSeries[0]) / (costSeries[0] || 1)) * 100 : 0;
  const hitDelta = hitSeries.length ? lastHit - hitSeries[0] : 0;
  const highDelta = highSeries.length ? lastHigh - highSeries[0] : 0;

  const costColor = costDelta > 10 ? 'var(--danger)' : (costDelta > 0 ? 'var(--warning)' : 'var(--success)');
  const hitColor = hitDelta < -5 ? 'var(--warning)' : (hitDelta < 0 ? 'var(--text-tertiary)' : 'var(--success)');
  const highColor = highDelta > 0 ? 'var(--danger)' : (highDelta < 0 ? 'var(--success)' : 'var(--text-tertiary)');

  return `
    <div class="section-direction">
      <div class="section-head">
        <div class="section-title-big">Ce qui se passe aujourd'hui</div>
      </div>
      <div class="narrative-row">
        <div class="narrative-card">
          <div class="narrative-head">
            <div class="narrative-title">Cout LLM mois</div>
            <div class="narrative-delta" style="color:${costColor}">${costDelta >= 0 ? '+' : ''}${costDelta.toFixed(0)}%</div>
          </div>
          <div class="narrative-value">${formatUsd(lastCost)}</div>
          <div style="margin-top:8px">${renderLineChart(costSeries, 220, 50, '#e85c5c')}</div>
          <div class="narrative-text">${narrativeCost(trends)}</div>
        </div>
        <div class="narrative-card">
          <div class="narrative-head">
            <div class="narrative-title">Hit rate cache</div>
            <div class="narrative-delta" style="color:${hitColor}">${hitDelta >= 0 ? '+' : ''}${hitDelta.toFixed(0)}pt</div>
          </div>
          <div class="narrative-value">${formatPct(lastHit)}</div>
          <div style="margin-top:8px">${renderLineChart(hitSeries, 220, 50, '#d4a95c')}</div>
          <div class="narrative-text">${narrativeHitRate(trends)}</div>
        </div>
        <div class="narrative-card">
          <div class="narrative-head">
            <div class="narrative-title">Clients haute urgence</div>
            <div class="narrative-delta" style="color:${highColor}">${highDelta >= 0 ? '+' : ''}${highDelta}</div>
          </div>
          <div class="narrative-value">${formatInt(lastHigh)}</div>
          <div style="margin-top:8px">${renderLineChart(highSeries, 220, 50, '#4a90e2')}</div>
          <div class="narrative-text">${narrativeHigh(trends)}</div>
        </div>
      </div>
    </div>
  `;
}

// === Section 2 : Signaux techniques (latence, scheduler, derive Evidently) ===

function renderSignauxSection(kpi) {
  const latencyMs = kpi.ml_ops.avg_latency_ms;
  const latencyColor = latencyMs > 3000 ? 'var(--danger)' : (latencyMs > 1500 ? 'var(--warning)' : 'var(--success)');

  const drift = kpi.drift;
  const driftFeatures = drift.drifted_features && drift.drifted_features.length
    ? drift.drifted_features.map(f => `<span class="drift-feature">${f}</span>`).join('')
    : '<span class="drift-feature-none">Aucune feature derivee</span>';
  const driftShare = drift.nb_features_total > 0
    ? `${drift.nb_features_drifted}/${drift.nb_features_total} features . ${(drift.share_drifted * 100).toFixed(0)}%`
    : 'n/a';

  const reportLink = drift.report_available
    ? `<a href="/monitoring/drift/report" target="_blank" class="evidently-link">Voir rapport Evidently →</a>`
    : '';

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
          <div class="signal-label">Scheduler APScheduler</div>
          <div class="signal-value" style="color:var(--success);font-size:14px;margin-top:6px">OK . jobs actifs</div>
        </div>
      </div>
      <div class="signal-wide-card">
        <div class="signal-wide-head">
          <div class="signal-label">Derive features (Evidently)</div>
          <div class="signal-wide-meta">
            <span style="color:var(--text-tertiary);font-variant-numeric:tabular-nums">${driftShare}</span>
            ${reportLink}
          </div>
        </div>
        <div class="drift-features">${driftFeatures}</div>
        ${drift.computed_at ? `<div class="signal-wide-footer">Dernier calcul : ${new Date(drift.computed_at).toLocaleString('fr-FR')} . Scheduler lance toutes les heures</div>` : ''}
      </div>
    </div>
  `;
}

// === Top 10 clients ===

function renderTopList(topClients) {
  if (!topClients.length) {
    return `
      <div class="section-direction">
        <div class="section-head"><div class="section-title-big">Top 10 clients a risque</div></div>
        <div class="top-list"><div class="loading-state">Aucun client a afficher.</div></div>
      </div>
    `;
  }
  const maxScore = Math.max(...topClients.map(c => c.score_churn));
  const rows = topClients.map((c, idx) => {
    const barWidth = (c.score_churn / maxScore) * 100;
    const scorePct = (c.score_churn * 100).toFixed(0);
    return `
      <div class="top-row" data-id="${c.id}">
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
      <div class="section-head"><div class="section-title-big">Top 10 clients a risque (toutes regions)</div></div>
      <div class="top-list">${rows}</div>
    </div>
  `;
}

// === Section 3 : Synthese chiffree (en bas) ===

function renderSyntheseSection(kpi) {
  const avgCostPerDay = kpi.ml_ops.cost_llm_mois_courant_usd / 30;
  const costAlert = kpi.ml_ops.cost_llm_24h_usd > avgCostPerDay * 2;
  return `
    <div class="section-direction">
      <div class="section-head"><div class="section-title-big">Synthese chiffree</div></div>
      <div class="kpi-grid-direction">
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Portefeuille total</div>
          <div class="kpi-value">${formatInt(kpi.portfolio.total_clients)}</div>
          <div class="kpi-sub-direction">score moyen ${kpi.portfolio.score_moyen}</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Haute urgence</div>
          <div class="kpi-value alert">${formatInt(kpi.portfolio.nb_high)}</div>
          <div class="kpi-sub-direction">${kpi.portfolio.pct_high}% du portefeuille</div>
        </div>
        <div class="kpi-card-direction">
          <div class="kpi-head-label">Cout LLM 24h</div>
          <div class="kpi-value ${costAlert ? 'alert' : ''}">${formatUsd(kpi.ml_ops.cost_llm_24h_usd)}</div>
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
      <div class="section-direction" style="margin-bottom:16px">
        <div class="section-head">
          <div class="section-title-big">Vue d'ensemble</div>
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
