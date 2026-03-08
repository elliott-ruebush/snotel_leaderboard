import { StationEntry, CategoryData, LeaderboardData, MetricConfig, CategoryFilter } from './types';
import { convert, getSuffix, stationUrl } from './utils';

let currentUnit: 'metric' | 'imperial' = 'metric';
let cachedData: LeaderboardData | null = null;
let currentFilter: CategoryFilter = 'all';

const METRIC_CONFIGS: MetricConfig[] = [
    // --- Snow Depth Group ---
    {
        id: 'deepest_dumps_24h',
        title: 'Deepest Dumps (24h)',
        icon: '❄️',
        desc: 'Highest magnitude snow depth changes in the past 24 hours.',
        type: 'snow',
        filters: ['all', 'snow', '24h']
    },
    {
        id: 'deepest_dumps_48h',
        title: 'Deepest Dumps (48h)',
        icon: '🌨️',
        desc: 'Highest magnitude snow depth change over the past 48 hours.',
        type: 'snow',
        filters: ['all', 'snow', '48h']
    },
    {
        id: 'deepest_dumps_7d',
        title: 'Deepest Dumps (7d)',
        icon: '☃️',
        desc: 'Highest magnitude snow depth change over the past 7 days.',
        type: 'snow',
        filters: ['all', 'snow', '7d']
    },
    {
        id: 'base_builders',
        title: 'Biggest Bases (Snow Depth)',
        icon: '🏔️',
        desc: 'Stations with the highest current snow depth.',
        type: 'snow',
        filters: ['all', 'snow']
    },
    // --- SWE Group ---
    {
        id: 'swe_trend_24h',
        title: 'SWE Trend (24h)',
        icon: '💧',
        desc: 'Highest magnitude Snow Water Equivalent change over the past 24 hours.',
        type: 'swe',
        filters: ['all', 'swe', '24h']
    },
    {
        id: 'swe_trend_48h',
        title: 'SWE Trend (48h)',
        icon: '🌊',
        desc: 'Highest magnitude Snow Water Equivalent change over the past 48 hours.',
        type: 'swe',
        filters: ['all', 'swe', '48h']
    },
    {
        id: 'swe_trend_7d',
        title: 'SWE Trend (7d)',
        icon: '⛲',
        desc: 'Highest magnitude Snow Water Equivalent change over the past 7 days.',
        type: 'swe',
        filters: ['all', 'swe', '7d']
    },
    {
        id: 'water_bearers',
        title: 'Snow Storage (Top SWE)',
        icon: '🐋',
        desc: 'Stations with the highest current Snow Water Equivalent (water weight).',
        type: 'swe',
        filters: ['all', 'swe']
    },
    // --- Historical Group ---
    {
        id: 'historical_consistency',
        title: 'Historical Consistency (SD)',
        icon: '📈',
        desc: 'Standard deviation of peak snow depth per Water Year. Higher means more unpredictable seasons.',
        type: 'snow',
        showAllTime: true,
        filters: ['all', 'historical']
    },
    {
        id: 'live_z_score',
        title: 'Live Anomaly (Z-Score)',
        icon: '🎯',
        desc: 'Z-score of current SWE compared to historical SWE for the same exact calendar day.',
        type: 'zscore',
        filters: ['all', 'historical', 'swe']
    }
];

const FILTER_OPTIONS: { id: CategoryFilter; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'snow', label: 'Snow Depth' },
    { id: 'swe', label: 'Water (SWE)' },
    { id: '24h', label: '24h Change' },
    { id: '48h', label: '48h Change' },
    { id: '7d', label: '7 Day Change' },
    { id: 'historical', label: 'Historical' }
];

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('unit-toggle') as HTMLInputElement | null;
    if (toggle) {
        toggle.addEventListener('change', () => {
            currentUnit = toggle.checked ? 'imperial' : 'metric';
            renderDashboard();
        });
    }

    renderFilterTabs();
    fetchLeaderboard();
});

function renderFilterTabs() {
    const container = document.getElementById('category-filters');
    if (!container) return;

    container.innerHTML = '';

    FILTER_OPTIONS.forEach(option => {
        const btn = document.createElement('button');
        btn.className = `filter-btn ${currentFilter === option.id ? 'active' : ''}`;
        btn.textContent = option.label;
        btn.addEventListener('click', () => {
            currentFilter = option.id;
            renderFilterTabs(); // Update active class
            renderDashboard(); // Re-render content
        });
        container.appendChild(btn);
    });
}

async function fetchLeaderboard() {
    try {
        const response = await fetch(`leaderboard.json?t=${new Date().getTime()}`);
        if (!response.ok) throw new Error('Data not available');
        cachedData = await response.json();
        renderMetadata();
        renderDashboard();
    } catch (error) {
        console.error('Error fetching leaderboard:', error);
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.textContent = 'Error loading data. Make sure leaderboard.json exists.';
    }
}

function renderMetadata() {
    if (!cachedData || !cachedData.metadata) return;
    const meta = cachedData.metadata;
    const bar = document.getElementById('metadata-bar');
    if (!bar) return;

    const d = new Date(meta.generated_at);
    const dateStr = d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
    const timeStr = String(d.getHours()).padStart(2, '0') + ':' +
        String(d.getMinutes()).padStart(2, '0') + ':' +
        String(d.getSeconds()).padStart(2, '0');
    const tz = d.toLocaleTimeString('en-us', { timeZoneName: 'short' }).split(' ').pop();

    const genDisplay = `${dateStr} ${timeStr} ${tz}`;
    const maxDate = meta.max_date; // Already YYYY-MM-DD

    bar.innerHTML = `
        <div class="metadata-item">Generated: <span>${genDisplay}</span></div>
        <div class="metadata-item">Latest Data: <span>${maxDate}</span></div>
        <div class="metadata-item">Data: <a href="https://www.nrcs.usda.gov/state-offices/nevada/what-is-a-snotel-station" target="_blank">NRCS SNOTEL</a> • <a href="https://github.com/egagli/snotel_ccss_stations" target="_blank">Eric Gagliano SNOTEL/CCSS Data</a></div>
        <div class="metadata-item">Methodology: <a href="#data-description">Data Info and Validation</a></div>
        <div class="metadata-item">Stations: <span>${meta.total_stations}</span></div>
    `;
}



function renderDashboard() {
    if (!cachedData) return;

    const dashboard = document.getElementById('dashboard');
    if (!dashboard) return;
    dashboard.innerHTML = '';

    METRIC_CONFIGS.forEach(config => {
        // Apply filter logic here
        if (!config.filters.includes(currentFilter)) {
            return;
        }

        const item = cachedData![config.id] as CategoryData | undefined;
        if (item) {
            const card = createLeaderboardCard(config, item);
            dashboard.appendChild(card);
        }
    });
}

function createLeaderboardCard(config: MetricConfig, categoryData: CategoryData): HTMLElement {
    const card = document.createElement('div');
    card.className = 'glass-card';

    const header = document.createElement('div');
    header.className = 'card-title';
    header.innerHTML = `<span class="icon">${config.icon}</span> ${config.title}`;

    const desc = document.createElement('p');
    desc.className = 'station-meta';
    desc.style.marginBottom = '1.2rem';
    desc.textContent = config.desc;

    const table = document.createElement('table');
    table.className = 'leaderboard-table';

    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th class="rank-cell">#</th>
            <th>Station</th>
            <th class="metric-col">${currentUnit === 'metric' ? 'Metric' : 'Imperial'}</th>
        </tr>
    `;

    const tbody = document.createElement('tbody');

    // Add TOP 10
    categoryData.top.forEach((item, index) => {
        tbody.appendChild(createRow(item, index + 1, config));
    });

    // Add Ellipsis / Separator
    const sep = document.createElement('tr');
    sep.innerHTML = `<td colspan="3" style="text-align: center; color: var(--text-muted); padding: 4px; font-size: 0.8rem;">•••</td>`;
    tbody.appendChild(sep);

    // Add BOTTOM 5
    const totalCount = categoryData.total_count || 100;
    categoryData.bottom.forEach((item, index) => {
        const rank = totalCount - (categoryData.bottom.length - index - 1);
        tbody.appendChild(createRow(item, rank, config));
    });

    table.appendChild(thead);
    table.appendChild(tbody);

    card.appendChild(header);
    card.appendChild(desc);

    if (categoryData.notes) {
        const notes = document.createElement('div');
        notes.className = 'cleaning-note';
        notes.textContent = categoryData.notes;
        card.appendChild(notes);
    }

    card.appendChild(table);

    return card;
}

function createRow(item: StationEntry, rank: number, config: MetricConfig): HTMLElement {
    const tr = document.createElement('tr');

    const convertedVal = convert(item.value, config.type, currentUnit);
    const suffix = getSuffix(config.type, currentUnit);

    // Dynamic precision based on metric type and ID
    let precision = 1;
    if (config.type === 'zscore') {
        precision = 2;
    } else if (config.type === 'elevation' || config.type === 'snow') {
        precision = 0; // Show elevation and snow depth to nearest full unit (ft/in or m/cm)
    } else if (config.type === 'swe') {
        precision = 1; // SWE changes and base use 1 decimal (nearest mm or 0.1 inch)
    }

    const displayVal = convertedVal !== null ?
        (convertedVal.toFixed(precision) + suffix) : 'N/A';

    const elev = convert(item.elevation_m, 'elevation', currentUnit);
    const elevSuffix = getSuffix('elevation', currentUnit);
    const elevDisplay = elev !== null ? `${elev.toFixed(0)}${elevSuffix}` : 'N/A';

    let extraInfo = '';
    if (config.showAllTime && item.all_time_max !== undefined) {
        const max = convert(item.all_time_max, config.type, currentUnit);
        const min = convert(item.all_time_min, config.type, currentUnit);
        const maxYr = item.all_time_max_year;
        const minYr = item.all_time_min_year;

        if (max !== null && min !== null) {
            // Use 0 precision for historical peak snow depth bases
            extraInfo = `<div class="station-meta" style="color: var(--accent-orange); font-size: 0.75rem;">
                Peak Snow Depth Range: ${min.toFixed(0)}${suffix} (${minYr}) - ${max.toFixed(0)}${suffix} (${maxYr})
            </div>`;
        }
    }

    if (item.current_swe !== undefined && item.hist_mean_swe !== undefined) {
        const current = convert(item.current_swe, 'swe', currentUnit);
        const average = convert(item.hist_mean_swe, 'swe', currentUnit);
        const sweSuffix = getSuffix('swe', currentUnit);
        if (current !== null && average !== null) {
            extraInfo += `<div class="station-meta" style="color: var(--accent-cyan); font-size: 0.75rem;">
                Current: ${current.toFixed(1)}${sweSuffix} vs Avg: ${average.toFixed(1)}${sweSuffix}
            </div>`;
        }
    }

    const url = stationUrl(item.station_id);
    const reasons = item.qc_flags && item.qc_flags.length > 0 
        ? item.qc_flags.join(', ') 
        : 'Anomalies detected.';
    
    const qcNote = item.is_flagged 
        ? `<div class="qc-flag-note">⚠️ ${reasons}</div>`
        : '';

    tr.innerHTML = `
        <td class="rank-cell" style="font-size: 0.8rem;">${rank}</td>
        <td class="station-cell">
            <div class="station-name" style="font-size: 0.95rem;">${item.name}</div>
            <div class="station-meta" style="font-size: 0.75rem;"><a href="${url}" target="_blank" rel="noopener noreferrer" class="station-id-link">${item.station_id}</a> • ${item.state} • ${elevDisplay}${item.data_date ? ' • ' + item.data_date : ''}</div>
            ${extraInfo}
            ${qcNote}
        </td>
        <td class="value-cell" style="font-size: 1rem;">
            ${displayVal}
        </td>
    `;
    return tr;
}
