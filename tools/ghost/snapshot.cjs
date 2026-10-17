'use strict';
// Saves the public Ghost market desk data as static JSON for seattlesinner.com/markets/.
// Usage: node tools/ghost/snapshot.cjs [core|countries|all]
const fs = require('node:fs');
const path = require('node:path');
const {createPublicApp} = require('./market-desk/public-app.cjs');
const {countries} = require('./country-desk/catalog.js');

const OUT = path.join(__dirname, '..', '..', 'markets', 'data');
const mode = process.argv[2] || 'core';
const app = createPublicApp({assets: {}});
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function grab(route) {
  const res = await app.fetch(new Request('https://public.local' + route));
  if (!res.ok) throw Error(route + ' -> ' + res.status);
  return res.json();
}

function save(file, data) {
  const p = path.join(OUT, file);
  fs.mkdirSync(path.dirname(p), {recursive: true});
  fs.writeFileSync(p, JSON.stringify(data));
}

async function core() {
  for (const [route, file] of [
    ['/api/world-news', 'world-news.json'],
    ['/api/market-overview', 'market-overview.json'],
    ['/api/investment-board', 'investment-board.json'],
  ]) {
    try { save(file, await grab(route)); console.log('ok', file); }
    catch (e) { console.log('kept old', file, String(e.message || e)); }
  }
}

async function countryFiles() {
  let ok = 0;
  for (const c of countries) {
    try {
      const d = await grab('/api/country-desk?country=' + c.code + '&topic=all');
      if (d && d.economy && d.news) { save('country/' + c.code + '.json', d); ok++; }
    } catch (e) { console.log('skip', c.code, String(e.message || e)); }
    await sleep(1500);
  }
  console.log('countries saved', ok, 'of', countries.length);
}

(async () => {
  if (mode === 'core' || mode === 'all') await core();
  if (mode === 'countries' || mode === 'all') await countryFiles();
})();
