// Exercise the actual form/render/copy/download flow with a minimal DOM adapter.
// This is a deterministic rendering contract, not a real-browser smoke test.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const source = fs.readFileSync(new URL('../docs/verify/verify.js', import.meta.url), 'utf8');
const strict = JSON.parse(fs.readFileSync(new URL('../profiles/1.0.0/example-report.json', import.meta.url)));
const baseline = JSON.parse(fs.readFileSync(new URL('../fixtures/compatibility/legacy-baseline.json', import.meta.url)));
const legacy = baseline.results.hosted.find(item => item.body?.guide?.achieved_level === 4).body;
class Element {
  value = ''; textContent = ''; className = ''; hidden = false; children = []; listeners = {};
  addEventListener(name, fn) { this.listeners[name] = fn; }
  appendChild(child) { this.children.push(child); }
  removeChild(child) { this.children = this.children.filter(item => item !== child); }
  click() { this.clicked = true; }
}
const elements = new Map();
const element = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
const copied = [], downloaded = [];
let response;
const context = {
  document: { getElementById: element, createElement: () => new Element(), body: new Element() },
  fetch: async () => ({ ok: true, status: 200, json: async () => response }),
  navigator: { clipboard: { writeText: async text => { copied.push(text); } } },
  Blob,
  URL: { createObjectURL: blob => { downloaded.push(blob); return 'blob:test'; }, revokeObjectURL: () => {} },
};
vm.runInNewContext(source, context);
for (const report of [legacy, strict, legacy, strict]) {
  response = report;
  element('guide-url').value = report.input.url;
  element('verify-form').listeners.submit({ preventDefault() {} });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(element('verify-compact').textContent, report.compact_report);
  assert.deepEqual(JSON.parse(element('verify-json').textContent), report);
  assert.equal(element('verify-headline').textContent.startsWith('Profile 1.0.0'), report === strict);
  element('verify-copy-compact').listeners.click();
  element('verify-download').listeners.click();
  assert.equal(copied.at(-1), report.compact_report);
  assert.deepEqual(JSON.parse(await downloaded.at(-1).text()), report);
  assert.equal(element('verify-submit').disabled, false);
}
console.log('Verify UI contract passed: legacy/strict form, render, copy, download, and repeat requests.');
