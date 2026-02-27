import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';

const html = readFileSync('templates/index.html', 'utf8');
const css = readFileSync('static/css/timeline.css', 'utf8');
const age = readFileSync('static/js/age.js', 'utf8');
const timeline = readFileSync('static/js/timeline.js', 'utf8');
const pivot = readFileSync('static/js/pivot.js', 'utf8');
const chat = readFileSync('static/js/chat.js', 'utf8');

const inlined = html
  .replace('<link rel="stylesheet" href="/static/css/timeline.css" />', `<style>${css}</style>`)
  .replace('<script type="module" src="/static/js/chat.js"></script>', `<script type="module">${age}\n${timeline}\n${pivot}\n${chat.replace("import { initAgeUI } from './age.js';", '').replace("import { renderTimeline } from './timeline.js';", '').replace("import { runPivot } from './pivot.js';", '')}</script>`);

mkdirSync('dist', { recursive: true });
writeFileSync('dist/index.html', inlined);
console.log('dist/index.html hazır');
