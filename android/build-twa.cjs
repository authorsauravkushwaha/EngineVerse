#!/usr/bin/env node
/* Build-time only. Generate a Bubblewrap Trusted Web Activity from the ACTUAL
 * HTTPS application, not the GitHub Pages reading copy. No key is committed. */
'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const net = require('node:net');
const path = require('node:path');

function settings(env) {
  const origin = (env.ENGINEVERSE_APP_URL || '').replace(/\/$/, '');
  if (!/^https:\/\/[A-Za-z0-9.-]+$/.test(origin)) {
    throw new Error('A public root HTTPS ENGINEVERSE_APP_URL is required for the APK.');
  }
  const host = new URL(origin).hostname;
  if (net.isIP(host) || !host.includes('.') ||
      host.endsWith('.local') || host.endsWith('.internal') ||
      host.endsWith('.localhost') || host.split('.').some((label) =>
        !/^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/i.test(label))) {
    throw new Error('A public root HTTPS ENGINEVERSE_APP_URL is required for the APK.');
  }
  const pkg = env.ENGINEVERSE_TWA_PACKAGE || '';
  if (!/^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$/.test(pkg)) {
    throw new Error('Set a stable, lowercase ENGINEVERSE_TWA_PACKAGE.');
  }
  const version = env.APK_VERSION || '';
  if (!/^v[0-9]+\.[0-9]+\.[0-9]+$/.test(version)) {
    throw new Error('APK_VERSION must be vMAJOR.MINOR.PATCH.');
  }
  const versionCode = Number(env.GITHUB_RUN_NUMBER);
  if (!Number.isSafeInteger(versionCode) || versionCode < 1 || versionCode > 2100000000) {
    throw new Error('GITHUB_RUN_NUMBER must be a positive Android version code.');
  }
  if (!env.ANDROID_SIGNING_KEYSTORE ||
      !/^[A-Za-z0-9_-]{1,64}$/.test(env.ANDROID_SIGNING_ALIAS || '')) {
    throw new Error('A signing keystore path and simple key alias are required.');
  }
  return { origin, pkg, version, versionCode,
    keystore: env.ANDROID_SIGNING_KEYSTORE, alias: env.ANDROID_SIGNING_ALIAS };
}

async function build() {
  const config = settings(process.env);
  const { TwaManifest, TwaGenerator, ConsoleLog } = require('@bubblewrap/core');
  const url = config.origin + '/manifest.webmanifest';
  const manifest = await TwaManifest.fromWebManifest(url);
  // Bubblewrap follows icon URLs. Reject a changed/compromised manifest that
  // tries to pull resources from another origin or package an unrelated site.
  if (manifest.host !== new URL(config.origin).host ||
      manifest.startUrl !== '/' || manifest.fullScopeUrl?.toString() !== config.origin + '/' ||
      !manifest.iconUrl || new URL(manifest.iconUrl).origin !== config.origin ||
      (manifest.maskableIconUrl && new URL(manifest.maskableIconUrl).origin !== config.origin)) {
    throw new Error('The hosted web manifest must point only to the root full app.');
  }
  manifest.packageId = config.pkg;
  manifest.appVersionCode = config.versionCode;
  manifest.appVersionName = config.version.slice(1);
  manifest.signingKey = { path: config.keystore, alias: config.alias };
  manifest.shortcuts = []; // no extra icon downloads or redirects from a mutable manifest
  manifest.enableNotifications = false; // the web app does not implement push
  manifest.fallbackType = 'customtabs';
  const directory = path.resolve(__dirname, '.generated');
  await fs.mkdir(directory, { recursive: true });
  const file = path.join(directory, 'twa-manifest.json');
  await manifest.saveToFile(file);
  await new TwaGenerator().createTwaProject(directory, manifest, new ConsoleLog('EngineVerse TWA'));
  const digest = crypto.createHash('sha1').update(await fs.readFile(file)).digest('hex');
  await fs.writeFile(path.join(directory, 'manifest-checksum.txt'), digest);
  console.log('Generated the Android project from the hosted HTTPS manifest.');
}

if (require.main === module) {
  if (process.argv.includes('--self-check')) {
    const example = settings({ ENGINEVERSE_APP_URL: 'https://learn.example.org/',
      ENGINEVERSE_TWA_PACKAGE: 'org.example.engineverse', APK_VERSION: 'v1.2.3',
      GITHUB_RUN_NUMBER: '12', ANDROID_SIGNING_KEYSTORE: '/tmp/keystore.jks',
      ANDROID_SIGNING_ALIAS: 'engineverse' });
    assert.equal(example.origin, 'https://learn.example.org');
    for (const bad of ['https://example.org/EngineVerse', 'http://example.org',
                       'https://127.0.0.1', 'https://other.internal']) {
      assert.throws(() => settings({ ...example, ENGINEVERSE_APP_URL: bad }));
    }
    console.log('Android TWA configuration self-check ok.');
  } else {
    build().catch((error) => { console.error(error.message); process.exitCode = 1; });
  }
}
module.exports = { settings };
