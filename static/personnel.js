'use strict';
const reports = JSON.parse(document.getElementById('report-data').textContent);
const $ = id => document.getElementById(id);
const fmt = value => value === null ? '-' : new Intl.NumberFormat('ru-RU', {maximumFractionDigits: 1}).format(value);
const escapeHtml = value => String(value).replace(/[&<>"']/g, character => ({
  '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
}[character]));

const metrics = [
  ['headcount', 'Среднесписочная численность'],
  ['dismissed', 'Уволено за период'],
  ['hired', 'Принято за период']
];
const colors = {headcount: 'personnel-headcount', dismissed: 'personnel-dismissed', hired: 'personnel-hired'};

function renderReport(report) {
  $('demo-tag').hidden = !report.demo;
  $('warnings').replaceChildren();
  report.warnings.forEach(warning => {
    const message = document.createElement('p');
    message.className = 'notice';
    message.textContent = warning;
    $('warnings').append(message);
  });

  const data = report.personnel;
  $('personnel-kpis').innerHTML = metrics.map(([key, label]) =>
    `<article class="metric"><h2 class="metric__label">${label}</h2><p class="metric__value">${fmt(data.totals[key])}</p><p class="metric__note">По строке «ИТОГО», человек</p></article>`
  ).join('');

  const categories = data.records.filter(row => !row.total && !row.subcategory);
  const maxValue = Math.max(1, ...categories.flatMap(row => metrics.map(([key]) => row[key] || 0)));
  const hasValues = categories.some(row => metrics.some(([key]) => row[key] !== null));
  $('personnel-category-chart').innerHTML = hasValues
    ? `<div class="personnel-legend">${metrics.map(([key, label]) => `<span><i class="${colors[key]}"></i>${label}</span>`).join('')}</div>` +
      categories.map(row => `<div class="personnel-group"><h3>${escapeHtml(row.role)}</h3>${metrics.map(([key, label]) => `<div class="personnel-bar-row"><span>${label}</span><div class="bar-track"><div class="bar ${colors[key]}" style="width:${Math.max(0, (row[key] || 0) / maxValue * 100)}%"></div><span class="bar-value">${fmt(row[key])}</span></div></div>`).join('')}</div>`).join('')
    : '<div class="empty-chart">Числовые показатели в этой книге не заполнены.</div>';

  const reasons = data.reason_frequencies || [];
  const maxFrequency = Math.max(1, ...reasons.map(item => item.count));
  const topFrequency = reasons.length ? reasons[0].count : 0;
  $('personnel-reason-chart').innerHTML = reasons.length
    ? reasons.map(item => `<div class="personnel-reason-row${item.count === topFrequency ? ' personnel-reason-row--top' : ''}"><span class="personnel-reason-label">${escapeHtml(item.reason)}${item.count === topFrequency ? '<strong>Наиболее частая</strong>' : ''}</span><div class="bar-track"><div class="bar personnel-reason-bar" style="width:${item.count / maxFrequency * 100}%"></div><span class="bar-value">${fmt(item.count)}</span></div></div>`).join('')
    : '<div class="empty-chart">В отчёте не указаны причины увольнения.</div>';

  $('personnel-detail-body').innerHTML = data.records.map(row =>
    `<tr class="${row.total ? 'personnel-total' : ''}"><td class="${row.subcategory ? 'personnel-subcategory' : ''}">${escapeHtml(row.role)}</td>${metrics.map(([key]) => `<td>${fmt(row[key])}</td>`).join('')}<td>${escapeHtml(row.reasons || '-')}</td></tr>`
  ).join('') || '<tr><td colspan="5">Строки категорий не найдены</td></tr>';
}

if (reports.length) {
  const select = $('report-select');
  select.addEventListener('change', () => renderReport(reports[Number(select.value)]));
  renderReport(reports[0]);
}
