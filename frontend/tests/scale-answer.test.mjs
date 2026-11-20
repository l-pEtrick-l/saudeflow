import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { mkdtempSync, rmSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { build } from 'esbuild';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const folder = mkdtempSync(fileURLToPath(new URL('../.scale-test-', import.meta.url)));
after(() => rmSync(folder, { recursive: true, force: true }));
await build({ entryPoints: [fileURLToPath(new URL('../src/components/ScaleAnswer.tsx', import.meta.url))], outfile: `${folder}/scale.cjs`, bundle: true, packages: 'external', format: 'cjs', platform: 'node', jsx: 'automatic' });
const { ScaleAnswer } = createRequire(import.meta.url)(`${folder}/scale.cjs`);

function render(external_id, min, max, previous) {
  return renderToStaticMarkup(React.createElement(ScaleAnswer, {
    question: { id: external_id, external_id, options: [{ code: min }, { code: max }] },
    previous, disabled: false, onContinue() {},
  }));
}

test('temperature displays saved decimal value with Celsius and accessible text', () => {
  const html = render('febre_temperatura', 35, 41, 38.5);
  assert.match(html, /aria-valuetext="38,5 °C"/);
  assert.match(html, />38,5 °C<\/output>/);
  assert.match(html, /step="0.1"/);
  assert.match(html, /value="38.5"/);
});

test('unmeasured temperature can be skipped instead of submitting the default', () => {
  const html = render('febre_temperatura', 35, 41);
  assert.match(html, /disabled=""[^>]*>Continuar<\/button>/);
  assert.match(html, /Não medi a temperatura/);
});

test('pain uses a separate whole-number scale without Celsius', () => {
  const html = render('dor_intensidade', 0, 10, 6);
  assert.match(html, />6 de 10<\/output>/);
  assert.match(html, /step="1"/);
  assert.doesNotMatch(html, /°C/);
});
