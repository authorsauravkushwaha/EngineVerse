/* EngineVerse 3D — build every stored scene with the real renderer.
 *
 * check_engine3d.js proves the mesh maths is correct in isolation. This proves
 * something different and more useful: that the 48 scenes actually shipped in
 * seed_data/models_3d.py can all be turned into drawable geometry by the same
 * code the browser runs. A scene that validated as JSON but referenced a mesh
 * the renderer does not have, or asked for a polyline with one point, would
 * pass every Python test and still render as an empty box.
 *
 * Usage — Python writes the scenes, Node builds them:
 *
 *   python -c "import json,sys; sys.path[:0]=['backend','.']; \
 *     from seed_data.models_3d import MODELS_3D; \
 *     print(json.dumps(MODELS_3D))" | node scripts/check_scenes.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SOURCE = path.join(__dirname, "..", "backend", "static", "js", "engine3d.js");
const MAX_VERTS_PER_MESH = 20000;

/* --------------------------------------------------------------- DOM stub -- */

const noop = () => {};
const sandbox = { console, Math, Number, Array, Object, String, JSON, Float32Array, Uint16Array, isNaN, parseFloat, parseInt };
sandbox.window = {
  matchMedia: () => ({ matches: false }),
  requestAnimationFrame: () => 0,
  addEventListener: noop,
  devicePixelRatio: 1,
  WebGLRenderingContext: function WebGLRenderingContext() {},
};
sandbox.document = {
  readyState: "complete",
  hidden: false,
  addEventListener: noop,
  querySelectorAll: () => [],
  createElement: () => ({ style: {}, classList: { add: noop, remove: noop }, appendChild: noop }),
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(SOURCE, "utf8"), sandbox, { filename: SOURCE });
const BUILDERS = sandbox.window.EngineVerse3D.builders;

/* ------------------------------------------------------------------ checks -- */

const scenes = JSON.parse(fs.readFileSync(0, "utf8"));
const failures = [];
let objects = 0, meshes = 0, vertices = 0, triangles = 0;

const known = new Set(Object.keys(BUILDERS));

Object.keys(scenes).sort().forEach((slug) => {
  const entry = scenes[slug];
  if (!entry || !entry.scene || !Array.isArray(entry.scene.objects)) {
    failures.push(`${slug}: no scene`);
    return;
  }
  if (!entry.title || !entry.caption) failures.push(`${slug}: missing title or caption`);

  entry.scene.objects.forEach((spec, i) => {
    objects++;
    const tag = `${slug} object #${i} (${spec.mesh})`;
    if (!known.has(spec.mesh)) {
      failures.push(`${tag}: the renderer has no such mesh`);
      return;
    }
    let mesh;
    try { mesh = BUILDERS[spec.mesh](spec); } catch (err) {
      failures.push(`${tag}: builder threw ${err.message}`);
      return;
    }
    if (!mesh || !mesh.positions.length) {
      failures.push(`${tag}: built no geometry`);
      return;
    }
    meshes++;
    const count = mesh.positions.length / 3;
    vertices += count;
    if (mesh.mode === "triangles") triangles += mesh.indices.length / 3;
    if (count > MAX_VERTS_PER_MESH) {
      failures.push(`${tag}: ${count} vertices exceeds the cap`);
      return;
    }
    if (!mesh.positions.every(Number.isFinite)) { failures.push(`${tag}: non-finite position`); return; }
    if (!mesh.normals.every(Number.isFinite)) { failures.push(`${tag}: non-finite normal`); return; }
    if (mesh.indices.some((k) => !Number.isInteger(k) || k < 0 || k >= count)) {
      failures.push(`${tag}: index out of range`);
      return;
    }
    // Shaded geometry must have usable normals or it renders black.
    if (mesh.mode === "triangles") {
      let degenerate = 0;
      for (let k = 0; k < mesh.normals.length; k += 3) {
        if (Math.hypot(mesh.normals[k], mesh.normals[k + 1], mesh.normals[k + 2]) < 1e-4) degenerate++;
      }
      if (degenerate) failures.push(`${tag}: ${degenerate} zero-length normals`);
    }
  });

  (entry.scene.labels || []).forEach((label, i) => {
    if (!label.text || !Array.isArray(label.at) || label.at.length !== 3) {
      failures.push(`${slug} label #${i}: malformed`);
    }
  });
});

if (failures.length) {
  console.error(`FAIL  ${Object.keys(scenes).length} scenes, ${failures.length} problems`);
  failures.forEach((f) => console.error("  ✗ " + f));
  process.exit(1);
}
console.log(
  `OK  ${Object.keys(scenes).length} scenes, ${objects} objects, ${meshes} built, ` +
  `${vertices.toLocaleString("en-US")} vertices, ${triangles.toLocaleString("en-US")} triangles`,
);
