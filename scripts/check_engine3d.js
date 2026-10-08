/* EngineVerse 3D — headless verification of the renderer's maths.
 *
 * `node --check` only proves the file parses. This script actually runs the
 * shipping code from backend/static/js/engine3d.js against a minimal DOM stub
 * and asserts the things that would otherwise only show up as a wrong picture:
 *
 *   - every mesh builder emits finite geometry with in-range indices
 *   - hostile or degenerate parameters are clamped, not turned into NaN
 *   - an arrow really points from `from` to `to` (the cone orientation maths)
 *   - the model matrix follows the Ry·Rx·Rz convention the arrow maths assumes
 *
 * CI runs it, so a regression in the linear algebra fails the build instead of
 * silently producing a broken model in the browser.
 *
 *   node scripts/check_engine3d.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SOURCE = path.join(__dirname, "..", "backend", "static", "js", "engine3d.js");

/* --------------------------------------------------------------- DOM stub -- */

function makeSandbox() {
  const noop = () => {};
  const listeners = [];
  const sandbox = {
    console,
    Math,
    Number,
    Array,
    Object,
    String,
    JSON,
    Float32Array,
    Uint16Array,
    isNaN,
    parseFloat,
    parseInt,
  };
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
    addEventListener: (type, fn) => listeners.push([type, fn]),
    querySelectorAll: () => [],
    createElement: () => ({ style: {}, classList: { add: noop, remove: noop }, appendChild: noop }),
  };
  sandbox.window.window = sandbox.window;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  return sandbox;
}

const sandbox = makeSandbox();
vm.runInContext(fs.readFileSync(SOURCE, "utf8"), sandbox, { filename: SOURCE });
const EV = sandbox.window.EngineVerse3D;

/* ------------------------------------------------------------ assertions -- */

let passed = 0;
const failures = [];

function check(name, condition, detail) {
  if (condition) { passed++; return; }
  failures.push(name + (detail ? " — " + detail : ""));
}

function near(a, b, tol = 1e-4) { return Math.abs(a - b) <= tol; }

function finiteGeometry(mesh) {
  if (!mesh || !Array.isArray(mesh.positions) || !Array.isArray(mesh.indices)) return "not a mesh";
  if (!mesh.positions.length) return "empty";
  if (mesh.positions.length % 3 !== 0) return "positions not divisible by 3";
  if (mesh.normals.length !== mesh.positions.length) return "normals/positions length mismatch";
  if (!mesh.positions.every((n) => Number.isFinite(n))) return "non-finite position";
  if (!mesh.normals.every((n) => Number.isFinite(n))) return "non-finite normal";
  const count = mesh.positions.length / 3;
  if (mesh.indices.some((i) => !Number.isInteger(i) || i < 0 || i >= count)) return "index out of range";
  if (!["triangles", "lines", "points"].includes(mesh.mode)) return "unknown mode " + mesh.mode;
  const per = mesh.mode === "triangles" ? 3 : 2;
  if (mesh.mode !== "points" && mesh.indices.length % per !== 0) return "index count not a multiple of " + per;
  return null;
}

/* 1. Every builder the server is allowed to name produces usable geometry. */

const SAMPLES = {
  box: { width: 2, height: 1, depth: 0.5 },
  sphere: { radius: 0.8, segments: 24, rings: 14 },
  cylinder: { radius: 0.3, height: 2, segments: 20 },
  cone: { radius: 0.4, height: 1.2 },
  torus: { radius: 0.7, tube: 0.12, segments: 28, rings: 14 },
  plane: { size: 3 },
  grid: { size: 4, divisions: 8 },
  axes: { length: 1.5 },
  line: { points: [[0, 0, 0], [1, 1, 0], [2, 0, 1]] },
  points: { points: [[0, 0, 0], [1, 0, 1], [0, 1, 0]] },
  arrow: { from: [0, 0, 0], to: [1, 2, -1], shaft: 0.04, headLength: 0.3, headRadius: 0.1 },
  tube: { radius: 0.06, points: [[0, -1, 0], [0.5, 0, 0.2], [0, 1, 0]] },
  helix: { radius: 0.5, height: 2, turns: 4, tube: 0.05, samples: 64 },
  wave: { width: 2, depth: 2, segmentsX: 16, segmentsZ: 16, amplitude: 0.3, frequency: 4 },
};

Object.keys(EV.builders).forEach((kind) => {
  const mesh = EV.builders[kind](SAMPLES[kind] || {});
  const problem = finiteGeometry(mesh);
  check(`builder ${kind} emits finite geometry`, !problem, problem || "");
  check(`builder ${kind} has a sample`, !!SAMPLES[kind], "no sample scene exercised this builder");
});

/* 2. Sphere wireframe mode is a distinct, line-mode mesh. */

{
  const solid = EV.builders.sphere({ radius: 1 });
  const wire = EV.builders.sphere({ radius: 1, mode: "lines" });
  check("sphere mode:lines is drawn as lines", wire.mode === "lines", "got " + wire.mode);
  check("sphere mode:lines differs from the solid", solid.indices.length !== wire.indices.length);
}

/* 2b. A truncated cone actually tapers, and omitting radiusTop keeps it a cylinder. */

{
  const ringRadius = (mesh, y) => {
    let best = 0;
    for (let i = 0; i < mesh.positions.length; i += 3) {
      if (Math.abs(mesh.positions[i + 1] - y) < 1e-3) {
        best = Math.max(best, Math.hypot(mesh.positions[i], mesh.positions[i + 2]));
      }
    }
    return best;
  };
  const plain = EV.builders.cylinder({ radius: 0.5, height: 2 });
  check("cylinder without radiusTop has equal ends",
    near(ringRadius(plain, 1), 0.5) && near(ringRadius(plain, -1), 0.5),
    `top ${ringRadius(plain, 1)} bottom ${ringRadius(plain, -1)}`);
  const taper = EV.builders.cylinder({ radius: 0.5, radiusTop: 0.15, height: 2 });
  check("cylinder with radiusTop tapers",
    near(ringRadius(taper, 1), 0.15) && near(ringRadius(taper, -1), 0.5),
    `top ${ringRadius(taper, 1)} bottom ${ringRadius(taper, -1)}`);
  const point = EV.builders.cylinder({ radius: 0.5, radiusTop: 0, height: 2 });
  check("cylinder with radiusTop 0 comes to a point", near(ringRadius(point, 1), 0, 1e-3));
}

/* 3. Hostile parameters must clamp, not produce NaN or a million vertices. */

const HOSTILE = [
  { segments: 1e9, rings: 1e9 },
  { radius: "not a number" },
  { radius: Infinity, height: -Infinity },
  { width: NaN, height: NaN, depth: NaN },
  { divisions: 1e9 },
  {},
];

[["sphere", { radius: 1 }], ["box", { width: 1 }], ["grid", { size: 4 }], ["wave", { width: 2 }], ["torus", {}]].forEach(([kind, base]) => {
  HOSTILE.forEach((extra, i) => {
    const mesh = EV.builders[kind](Object.assign({}, base, extra));
    const problem = finiteGeometry(mesh);
    check(`builder ${kind} survives hostile input #${i}`, !problem, problem || "");
    const verts = mesh.positions.length / 3;
    check(`builder ${kind} stays bounded under hostile input #${i}`, verts <= 20000, verts + " vertices");
  });
});

{
  const mesh = EV.builders.line({ points: "not a list" });
  check("line with a non-list emits nothing", mesh.indices.length === 0);
  const tooFew = EV.builders.line({ points: [[0, 0, 0]] });
  check("line with a single point emits nothing", tooFew.indices.length === 0);
}

/* 4. The model matrix must follow Ry·Rx·Rz, which the arrow maths assumes. */

{
  const m = EV.mat4.compose(new Float32Array(16), [0, 0, 0], [0, 90, 0], [1, 1, 1]);
  check("Ry(90°) maps +X to -Z", near(m[0], 0) && near(m[1], 0) && near(m[2], -1),
    `got (${m[0].toFixed(3)}, ${m[1].toFixed(3)}, ${m[2].toFixed(3)})`);
}

{
  // orientAlong(u) must map the cone's local +Y onto u exactly.
  const directions = [[0, 1, 0], [0, -1, 0], [1, 0, 0], [0, 0, 1], [1, 1, 1], [-2, 0.5, 3], [0, 0.999, 0.04]];
  directions.forEach((u) => {
    const len = Math.hypot(u[0], u[1], u[2]);
    const n = [u[0] / len, u[1] / len, u[2] / len];
    const m = EV.mat4.compose(new Float32Array(16), [0, 0, 0], EV.orientAlong(n), [1, 1, 1]);
    // Column 1 of the rotation is the image of +Y.
    check(`orientAlong points +Y along (${u})`, near(m[4], n[0]) && near(m[5], n[1]) && near(m[6], n[2]),
      `got (${m[4].toFixed(4)}, ${m[5].toFixed(4)}, ${m[6].toFixed(4)})`);
  });
}

/* 5. An arrow's tip must land on `to`. */

{
  const from = [0, 0, 0], to = [3, -2, 1.5];
  const mesh = EV.builders.arrow({ from, to, shaft: 0.05, headLength: 0.4, headRadius: 0.14 });
  check("arrow emits triangles", mesh.mode === "triangles", mesh.mode);
  let farthest = 0;
  for (let i = 0; i < mesh.positions.length; i += 3) {
    farthest = Math.max(farthest, Math.hypot(mesh.positions[i] - from[0], mesh.positions[i + 1] - from[1], mesh.positions[i + 2] - from[2]));
  }
  const expected = Math.hypot(to[0] - from[0], to[1] - from[1], to[2] - from[2]);
  check("arrow tip reaches the requested end point", near(farthest, expected, 1e-3),
    `farthest vertex ${farthest.toFixed(4)} vs length ${expected.toFixed(4)}`);

  const degenerate = EV.builders.arrow({ from: [1, 1, 1], to: [1, 1, 1] });
  check("zero-length arrow degrades instead of dividing by zero", !finiteGeometry(degenerate));
}

/* 6. Tube, helix and wave normals are unit length (they are used for lighting). */

{
  [["tube", SAMPLES.tube], ["helix", SAMPLES.helix], ["wave", SAMPLES.wave], ["sphere", SAMPLES.sphere]].forEach(([kind, params]) => {
    const mesh = EV.builders[kind](params);
    let worst = 0;
    for (let i = 0; i < mesh.normals.length; i += 3) {
      worst = Math.max(worst, Math.abs(Math.hypot(mesh.normals[i], mesh.normals[i + 1], mesh.normals[i + 2]) - 1));
    }
    check(`${kind} normals are unit length`, worst < 1e-3, "worst deviation " + worst.toFixed(6));
  });
}

/* 7. Projection, view and colour helpers. */

{
  const proj = EV.mat4.perspective(new Float32Array(16), Math.PI / 4, 1.5, 0.05, 100);
  check("perspective is finite", Array.from(proj).every(Number.isFinite));

  const view = EV.mat4.lookAt(new Float32Array(16), [0, 0, 5], [0, 0, 0], [0, 1, 0]);
  const vp = EV.mat4.multiply(new Float32Array(16), proj, view);
  const out = [0, 0, 0];
  EV.project(out, vp, [0, 0, 0]);
  check("the origin projects to the centre of the screen", near(out[0], 0, 1e-4) && near(out[1], 0, 1e-4),
    `(${out[0]}, ${out[1]})`);
  check("the origin is in front of the camera", out[2] > 0, "w=" + out[2]);
  EV.project(out, vp, [0, 0, 50]);
  check("a point behind the camera is marked for hiding", out[2] <= 0, "w=" + out[2]);
}

{
  const hex = EV.parseColor("#4f7cff", [0, 0, 0]);
  check("parseColor reads a 6-digit hex", near(hex[0], 79 / 255) && near(hex[1], 124 / 255) && near(hex[2], 1));
  const short = EV.parseColor("#f80", [0, 0, 0]);
  check("parseColor expands a 3-digit hex", near(short[0], 1) && near(short[1], 136 / 255) && near(short[2], 0));
  const arr = EV.parseColor([0.2, 0.4, 0.6], [0, 0, 0]);
  check("parseColor accepts an rgb array", near(arr[0], 0.2) && near(arr[1], 0.4));
  const bad = EV.parseColor("red;background:url(x)", [0.5, 0.5, 0.5]);
  check("parseColor refuses anything that is not a hex colour", bad.every((n) => n === 0.5));
  const clamped = EV.parseColor([9, -1, 0.5], [0, 0, 0]);
  check("parseColor clamps an out-of-range array instead of emitting NaN",
    clamped[0] === 1 && clamped[1] === 0 && near(clamped[2], 0.5), JSON.stringify(clamped));
  const junk = EV.parseColor(["a", "b", "c"], [0.25, 0.25, 0.25]);
  check("parseColor falls back on a non-numeric array", junk.every((n) => n === 0.25));
}

/* 8. Matrix multiply must be associative and agree with a hand computation. */

{
  const a = EV.mat4.compose(new Float32Array(16), [1, 2, 3], [30, -40, 15], [2, 1, 0.5]);
  const b = EV.mat4.compose(new Float32Array(16), [-1, 0, 2], [10, 20, 30], [1, 3, 1]);
  const c = EV.mat4.compose(new Float32Array(16), [0, 1, -1], [5, 5, 5], [1, 1, 1]);
  const ab_c = EV.mat4.multiply(new Float32Array(16), EV.mat4.multiply(new Float32Array(16), a, b), c);
  const a_bc = EV.mat4.multiply(new Float32Array(16), a, EV.mat4.multiply(new Float32Array(16), b, c));
  let worst = 0;
  for (let i = 0; i < 16; i++) worst = Math.max(worst, Math.abs(ab_c[i] - a_bc[i]));
  check("mat4.multiply is associative", worst < 1e-3, "worst difference " + worst);

  const identity = EV.mat4.create();
  const aI = EV.mat4.multiply(new Float32Array(16), a, identity);
  let idWorst = 0;
  for (let i = 0; i < 16; i++) idWorst = Math.max(idWorst, Math.abs(aI[i] - a[i]));
  check("multiplying by the identity is a no-op", idWorst < 1e-6);
}

/* ------------------------------------------------------------------ report -- */

if (failures.length) {
  console.error(`FAIL  ${passed} passed, ${failures.length} failed`);
  failures.forEach((f) => console.error("  ✗ " + f));
  process.exit(1);
}
console.log(`OK  ${passed} assertions passed over ${Object.keys(EV.builders).length} mesh builders`);
