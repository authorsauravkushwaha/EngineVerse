/* EngineVerse 3D — a self-contained WebGL renderer for engineering models.
 *
 * There is no three.js here and nothing is fetched from a CDN: the platform is
 * self-hosted, so the linear algebra, the mesh generators and the shading all
 * live in this file, with zero dependencies.
 *
 * A *scene* is plain JSON produced by the server and stored in the database
 * (table `models_3d`), so a model can be added or edited without touching this
 * code. The scene format is deliberately small:
 *
 *   { "camera": {"distance": 6, "yaw": 35, "pitch": 18, "fov": 45},
 *     "background": "#0b1224", "spin": 0.25, "ambient": 0.3,
 *     "objects": [{"mesh": "sphere", "radius": 0.4, "position": [0,0,0],
 *                  "color": "#4f7cff", "opacity": 0.9, "mode": "lines"}],
 *     "labels":  [{"text": "V", "at": [0, 1.6, 0]}] }
 *
 * Every numeric field is clamped here as well as on the server, so a malformed
 * or hostile scene degrades into a smaller model instead of hanging the tab.
 *
 * Progressive enhancement: without WebGL (or without JS) the page still shows
 * the title, the caption and the written explanation. The canvas is an
 * addition, never the only carrier of the information.
 */
(() => {
  "use strict";

  const REDUCED = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const DEG = Math.PI / 180;

  /* ------------------------------------------------------------------ math -- */

  const clamp = (v, lo, hi) => (v < lo ? lo : v > hi ? hi : v);

  const num = (v, fallback) => {
    const n = typeof v === "number" ? v : parseFloat(v);
    return Number.isFinite(n) ? n : fallback;
  };

  const mat4 = {
    create: () => new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]),

    multiply(out, a, b) {
      for (let c = 0; c < 4; c++) {
        const b0 = b[c * 4], b1 = b[c * 4 + 1], b2 = b[c * 4 + 2], b3 = b[c * 4 + 3];
        out[c * 4] = a[0] * b0 + a[4] * b1 + a[8] * b2 + a[12] * b3;
        out[c * 4 + 1] = a[1] * b0 + a[5] * b1 + a[9] * b2 + a[13] * b3;
        out[c * 4 + 2] = a[2] * b0 + a[6] * b1 + a[10] * b2 + a[14] * b3;
        out[c * 4 + 3] = a[3] * b0 + a[7] * b1 + a[11] * b2 + a[15] * b3;
      }
      return out;
    },

    perspective(out, fovy, aspect, near, far) {
      const f = 1 / Math.tan(fovy / 2);
      out.fill(0);
      out[0] = f / aspect;
      out[5] = f;
      out[10] = (far + near) / (near - far);
      out[11] = -1;
      out[14] = (2 * far * near) / (near - far);
      return out;
    },

    lookAt(out, eye, center, up) {
      let z0 = eye[0] - center[0], z1 = eye[1] - center[1], z2 = eye[2] - center[2];
      const zl = Math.hypot(z0, z1, z2) || 1;
      z0 /= zl; z1 /= zl; z2 /= zl;
      let x0 = up[1] * z2 - up[2] * z1, x1 = up[2] * z0 - up[0] * z2, x2 = up[0] * z1 - up[1] * z0;
      const xl = Math.hypot(x0, x1, x2);
      if (xl < 1e-6) { x0 = 1; x1 = 0; x2 = 0; } else { x0 /= xl; x1 /= xl; x2 /= xl; }
      const y0 = z1 * x2 - z2 * x1, y1 = z2 * x0 - z0 * x2, y2 = z0 * x1 - z1 * x0;
      out[0] = x0; out[1] = y0; out[2] = z0; out[3] = 0;
      out[4] = x1; out[5] = y1; out[6] = z1; out[7] = 0;
      out[8] = x2; out[9] = y2; out[10] = z2; out[11] = 0;
      out[12] = -(x0 * eye[0] + x1 * eye[1] + x2 * eye[2]);
      out[13] = -(y0 * eye[0] + y1 * eye[1] + y2 * eye[2]);
      out[14] = -(z0 * eye[0] + z1 * eye[1] + z2 * eye[2]);
      out[15] = 1;
      return out;
    },

    /** Model matrix from position, Euler rotation in degrees (Ry·Rx·Rz), scale. */
    compose(out, position, rotation, scale) {
      const cx = Math.cos(rotation[0] * DEG), sx = Math.sin(rotation[0] * DEG);
      const cy = Math.cos(rotation[1] * DEG), sy = Math.sin(rotation[1] * DEG);
      const cz = Math.cos(rotation[2] * DEG), sz = Math.sin(rotation[2] * DEG);
      const m00 = cy * cz + sy * sx * sz, m01 = -cy * sz + sy * sx * cz, m02 = sy * cx;
      const m10 = cx * sz, m11 = cx * cz, m12 = -sx;
      const m20 = -sy * cz + cy * sx * sz, m21 = sy * sz + cy * sx * cz, m22 = cy * cx;
      out[0] = m00 * scale[0]; out[1] = m10 * scale[0]; out[2] = m20 * scale[0]; out[3] = 0;
      out[4] = m01 * scale[1]; out[5] = m11 * scale[1]; out[6] = m21 * scale[1]; out[7] = 0;
      out[8] = m02 * scale[2]; out[9] = m12 * scale[2]; out[10] = m22 * scale[2]; out[11] = 0;
      out[12] = position[0]; out[13] = position[1]; out[14] = position[2]; out[15] = 1;
      return out;
    },

    /** Upper-left 3×3 of the inverse transpose, for lighting. */
    normalMatrix(out, m) {
      const a00 = m[0], a01 = m[1], a02 = m[2], a10 = m[4], a11 = m[5], a12 = m[6];
      const a20 = m[8], a21 = m[9], a22 = m[10];
      const b01 = a22 * a11 - a12 * a21, b11 = -a22 * a10 + a12 * a20, b21 = a21 * a10 - a11 * a20;
      const det = a00 * b01 + a01 * b11 + a02 * b21;
      if (!det) {
        out.set([1, 0, 0, 0, 1, 0, 0, 0, 1]);
        return out;
      }
      const id = 1 / det;
      out[0] = b01 * id;
      out[1] = (-a22 * a01 + a02 * a21) * id;
      out[2] = (a12 * a01 - a02 * a11) * id;
      out[3] = b11 * id;
      out[4] = (a22 * a00 - a02 * a20) * id;
      out[5] = (-a12 * a00 + a02 * a10) * id;
      out[6] = b21 * id;
      out[7] = (-a21 * a00 + a01 * a20) * id;
      out[8] = (a11 * a00 - a01 * a10) * id;
      return out;
    },
  };

  /** Clip-space projection of a point; out[2] <= 0 means "behind the camera". */
  function project(out, m, p) {
    const x = p[0], y = p[1], z = p[2];
    const w = m[3] * x + m[7] * y + m[11] * z + m[15] || 1e-6;
    out[0] = (m[0] * x + m[4] * y + m[8] * z + m[12]) / w;
    out[1] = (m[1] * x + m[5] * y + m[9] * z + m[13]) / w;
    out[2] = w;
    return out;
  }

  /* ---------------------------------------------------------------- meshes --
   * Each builder returns {positions, normals, indices, mode}, where mode is
   * "triangles" (shaded), "lines" (unlit skeleton) or "points". */

  const MAX_VERTS = 20000;
  const MAX_POINTS = 400;

  const tri = (a, b, c) => [a, b, c];

  function meshBox(w, h, d) {
    const x = Math.abs(w) / 2 || 0.001, y = Math.abs(h) / 2 || 0.001, z = Math.abs(d) / 2 || 0.001;
    const faces = [
      [[x, -y, z], [x, y, z], [-x, y, z], [-x, -y, z], [0, 0, 1]],
      [[-x, -y, -z], [-x, y, -z], [x, y, -z], [x, -y, -z], [0, 0, -1]],
      [[-x, -y, z], [-x, y, z], [-x, y, -z], [-x, -y, -z], [-1, 0, 0]],
      [[x, -y, -z], [x, y, -z], [x, y, z], [x, -y, z], [1, 0, 0]],
      [[-x, y, z], [x, y, z], [x, y, -z], [-x, y, -z], [0, 1, 0]],
      [[-x, -y, -z], [x, -y, -z], [x, -y, z], [-x, -y, z], [0, -1, 0]],
    ];
    const positions = [], normals = [], indices = [];
    faces.forEach((face, i) => {
      for (let k = 0; k < 4; k++) {
        positions.push(face[k][0], face[k][1], face[k][2]);
        normals.push(face[4][0], face[4][1], face[4][2]);
      }
      const o = i * 4;
      indices.push(o, o + 1, o + 2, o, o + 2, o + 3);
    });
    return { positions, normals, indices, mode: "triangles" };
  }

  function meshSphere(radius, segments, rings) {
    const positions = [], normals = [], indices = [];
    for (let j = 0; j <= rings; j++) {
      const phi = (j / rings) * Math.PI;
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        const nx = Math.sin(phi) * Math.cos(theta), ny = Math.cos(phi), nz = Math.sin(phi) * Math.sin(theta);
        positions.push(nx * radius, ny * radius, nz * radius);
        normals.push(nx, ny, nz);
      }
    }
    for (let j = 0; j < rings; j++) {
      for (let i = 0; i < segments; i++) {
        const a = j * (segments + 1) + i, b = a + segments + 1;
        indices.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    return { positions, normals, indices, mode: "triangles" };
  }

  /** Latitude/longitude wireframe. Reads better than a shaded ball when the
   *  ball stands for an atom, a node, a charge or a control volume. */
  function meshSphereLines(radius, segments, rings) {
    const positions = [], normals = [], indices = [];
    const at = (phi, theta) => [
      radius * Math.sin(phi) * Math.cos(theta),
      radius * Math.cos(phi),
      radius * Math.sin(phi) * Math.sin(theta),
    ];
    for (let j = 0; j <= rings; j++) {
      const phi = (j / rings) * Math.PI;
      const base = positions.length / 3;
      for (let i = 0; i <= segments; i++) {
        const p = at(phi, (i / segments) * Math.PI * 2);
        positions.push(p[0], p[1], p[2]); normals.push(0, 1, 0);
        if (i > 0) indices.push(base + i - 1, base + i);
      }
    }
    const meridianStep = Math.max(1, Math.floor(segments / 8));
    for (let i = 0; i < segments; i += meridianStep) {
      const theta = (i / segments) * Math.PI * 2;
      const base = positions.length / 3;
      for (let j = 0; j <= rings; j++) {
        const p = at((j / rings) * Math.PI, theta);
        positions.push(p[0], p[1], p[2]); normals.push(0, 1, 0);
        if (j > 0) indices.push(base + j - 1, base + j);
      }
    }
    return { positions, normals, indices, mode: "lines" };
  }

  function meshCylinder(rTop, rBottom, height, segments) {
    const positions = [], normals = [], indices = [];
    const half = Math.abs(height) / 2 || 0.001;
    const slope = (rBottom - rTop) / (height || 1);
    const inv = Math.hypot(1, slope) || 1;
    const ring = (y, r) => {
      const base = positions.length / 3;
      for (let i = 0; i <= segments; i++) {
        const t = (i / segments) * Math.PI * 2, cx = Math.cos(t), cz = Math.sin(t);
        positions.push(cx * r, y, cz * r);
        normals.push(cx / inv, slope / inv, cz / inv);
      }
      return base;
    };
    const bottom = ring(-half, rBottom), top = ring(half, rTop);
    for (let i = 0; i < segments; i++) {
      indices.push(bottom + i, top + i, bottom + i + 1, top + i, top + i + 1, bottom + i + 1);
    }
    const cap = (y, r, ny) => {
      const centre = positions.length / 3;
      positions.push(0, y, 0); normals.push(0, ny, 0);
      const base = positions.length / 3;
      for (let i = 0; i <= segments; i++) {
        const t = (i / segments) * Math.PI * 2;
        positions.push(Math.cos(t) * r, y, Math.sin(t) * r); normals.push(0, ny, 0);
        if (i === 0) continue;
        if (ny > 0) indices.push(centre, base + i, base + i - 1);
        else indices.push(centre, base + i - 1, base + i);
      }
    };
    if (rTop > 0) cap(half, rTop, 1);
    if (rBottom > 0) cap(-half, rBottom, -1);
    return { positions, normals, indices, mode: "triangles" };
  }

  function meshCone(radius, height, segments) {
    return meshCylinder(1e-4, Math.abs(radius) || 0.001, height, segments);
  }

  function meshTorus(R, r, uSegs, vSegs) {
    const positions = [], normals = [], indices = [];
    for (let j = 0; j <= vSegs; j++) {
      const v = (j / vSegs) * Math.PI * 2, cv = Math.cos(v), sv = Math.sin(v);
      for (let i = 0; i <= uSegs; i++) {
        const u = (i / uSegs) * Math.PI * 2, cu = Math.cos(u), su = Math.sin(u);
        positions.push((R + r * cv) * cu, r * sv, (R + r * cv) * su);
        normals.push(cv * cu, sv, cv * su);
      }
    }
    for (let j = 0; j < vSegs; j++) {
      for (let i = 0; i < uSegs; i++) {
        const a = j * (uSegs + 1) + i, b = a + uSegs + 1;
        indices.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    return { positions, normals, indices, mode: "triangles" };
  }

  function meshPlane(size) {
    const h = (Math.abs(size) || 1) / 2;
    return {
      positions: [-h, 0, h, h, 0, h, h, 0, -h, -h, 0, -h],
      normals: [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
      indices: [0, 1, 2, 0, 2, 3],
      mode: "triangles",
    };
  }

  function meshGrid(size, divisions) {
    const h = (Math.abs(size) || 1) / 2, step = (size || 1) / divisions;
    const positions = [], normals = [], indices = [];
    const segment = (a, b) => {
      const base = positions.length / 3;
      positions.push(a[0], a[1], a[2]); normals.push(0, 1, 0);
      positions.push(b[0], b[1], b[2]); normals.push(0, 1, 0);
      indices.push(base, base + 1);
    };
    for (let i = 0; i <= divisions; i++) {
      const p = -h + i * step;
      segment([p, 0, -h], [p, 0, h]);
      segment([-h, 0, p], [h, 0, p]);
    }
    return { positions, normals, indices, mode: "lines" };
  }

  function meshAxes(length) {
    const positions = [], normals = [], indices = [];
    const L = Math.abs(length) || 1;
    [[L, 0, 0], [0, L, 0], [0, 0, L]].forEach((tip) => {
      const base = positions.length / 3;
      positions.push(0, 0, 0); normals.push(0, 1, 0);
      positions.push(tip[0], tip[1], tip[2]); normals.push(0, 1, 0);
      indices.push(base, base + 1);
    });
    return { positions, normals, indices, mode: "lines" };
  }

  function meshPolyline(points) {
    const positions = [], normals = [], indices = [];
    for (let i = 0; i + 1 < points.length; i++) {
      const base = positions.length / 3;
      positions.push(points[i][0], points[i][1], points[i][2]); normals.push(0, 1, 0);
      positions.push(points[i + 1][0], points[i + 1][1], points[i + 1][2]); normals.push(0, 1, 0);
      indices.push(base, base + 1);
    }
    return { positions, normals, indices, mode: "lines" };
  }

  function meshPoints(points) {
    const positions = [], normals = [], indices = [];
    points.forEach((p, i) => {
      positions.push(p[0], p[1], p[2]); normals.push(0, 1, 0); indices.push(i);
    });
    return { positions, normals, indices, mode: "points" };
  }

  /** Sweep a circle along a polyline: helices, coil windings, field lines. */
  function meshTube(points, radius, radial) {
    if (points.length < 2) return meshPolyline(points);
    const positions = [], normals = [], indices = [];
    const rings = points.map((p, i) => {
      const prev = points[Math.max(0, i - 1)], next = points[Math.min(points.length - 1, i + 1)];
      let tx = next[0] - prev[0], ty = next[1] - prev[1], tz = next[2] - prev[2];
      const tl = Math.hypot(tx, ty, tz) || 1;
      tx /= tl; ty /= tl; tz /= tl;
      // Any up-vector that is not parallel to the tangent, then two crosses.
      const ux = Math.abs(ty) < 0.9 ? 0 : 1, uy = Math.abs(ty) < 0.9 ? 1 : 0, uz = 0;
      let bx = ty * uz - tz * uy, by = tz * ux - tx * uz, bz = tx * uy - ty * ux;
      const bl = Math.hypot(bx, by, bz) || 1;
      bx /= bl; by /= bl; bz /= bl;
      const cx = by * tz - bz * ty, cy = bz * tx - bx * tz, cz = bx * ty - by * tx;
      const base = positions.length / 3;
      for (let k = 0; k <= radial; k++) {
        const a = (k / radial) * Math.PI * 2, ca = Math.cos(a), sa = Math.sin(a);
        const nx = bx * ca + cx * sa, ny = by * ca + cy * sa, nz = bz * ca + cz * sa;
        positions.push(p[0] + nx * radius, p[1] + ny * radius, p[2] + nz * radius);
        normals.push(nx, ny, nz);
      }
      return base;
    });
    for (let i = 0; i + 1 < rings.length; i++) {
      for (let k = 0; k < radial; k++) {
        const a = rings[i] + k, b = rings[i + 1] + k;
        indices.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    return { positions, normals, indices, mode: "triangles" };
  }

  function helixPoints(radius, height, turns, samples) {
    const points = [];
    for (let i = 0; i <= samples; i++) {
      const t = i / samples, a = t * turns * Math.PI * 2;
      points.push([radius * Math.cos(a), (t - 0.5) * height, radius * Math.sin(a)]);
    }
    return points;
  }

  /** A cone built along +Y, re-oriented onto the vector from → to.
   *  Ry·Rx·Rz maps +Y to (sin ry·sin rx, cos rx, cos ry·sin rx), so choosing
   *  rx = acos(uy) and ry = atan2(ux, uz) points it exactly along the arrow. */
  function orientAlong(u) {
    const rx = Math.acos(clamp(u[1], -1, 1)) / DEG;
    const ry = Math.atan2(u[0], u[2]) / DEG;
    return [rx, ry, 0];
  }

  function meshArrow(from, to, shaft, headLength, headRadius) {
    const d = [to[0] - from[0], to[1] - from[1], to[2] - from[2]];
    const len = Math.hypot(d[0], d[1], d[2]);
    if (len < 1e-4) return meshPolyline([from, to]);
    const u = [d[0] / len, d[1] / len, d[2] / len];
    const head = Math.min(headLength, len * 0.6);
    const base = [to[0] - u[0] * head, to[1] - u[1] * head, to[2] - u[2] * head];
    const centre = [to[0] - u[0] * head * 0.5, to[1] - u[1] * head * 0.5, to[2] - u[2] * head * 0.5];
    const steps = 12, pts = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      pts.push([from[0] + (base[0] - from[0]) * t, from[1] + (base[1] - from[1]) * t, from[2] + (base[2] - from[2]) * t]);
    }
    return merge(meshTube(pts, shaft, 10), transformMesh(meshCone(headRadius, head, 16), orientAlong(u), centre));
  }

  function transformMesh(m, eulerDeg, offset) {
    const t = mat4.compose(mat4.create(), offset, eulerDeg, [1, 1, 1]);
    const positions = [], normals = [];
    for (let i = 0; i < m.positions.length; i += 3) {
      const x = m.positions[i], y = m.positions[i + 1], z = m.positions[i + 2];
      positions.push(t[0] * x + t[4] * y + t[8] * z + t[12], t[1] * x + t[5] * y + t[9] * z + t[13], t[2] * x + t[6] * y + t[10] * z + t[14]);
      const nx = m.normals[i], ny = m.normals[i + 1], nz = m.normals[i + 2];
      const lx = t[0] * nx + t[4] * ny + t[8] * nz;
      const ly = t[1] * nx + t[5] * ny + t[9] * nz;
      const lz = t[2] * nx + t[6] * ny + t[10] * nz;
      const l = Math.hypot(lx, ly, lz) || 1;
      normals.push(lx / l, ly / l, lz / l);
    }
    return { positions, normals, indices: m.indices.slice(), mode: m.mode };
  }

  function merge(a, b) {
    const offset = a.positions.length / 3;
    return {
      positions: a.positions.concat(b.positions),
      normals: a.normals.concat(b.normals),
      indices: a.indices.concat(b.indices.map((i) => i + offset)),
      mode: a.mode,
    };
  }

  /** Parametric height field: travelling waves, deflected beams, temperature
   *  surfaces. Normals are taken from a central difference, not approximated. */
  function meshWave(width, depth, segX, segZ, amplitude, frequency) {
    const positions = [], normals = [], indices = [];
    const hx = width / 2, hz = depth / 2;
    const height = (x, z) => amplitude * Math.sin(frequency * x) * Math.cos(frequency * z);
    for (let j = 0; j <= segZ; j++) {
      for (let i = 0; i <= segX; i++) {
        const x = -hx + (i / segX) * width, z = -hz + (j / segZ) * depth;
        positions.push(x, height(x, z), z);
        const e = 0.02;
        const dx = (height(x + e, z) - height(x - e, z)) / (2 * e);
        const dz = (height(x, z + e) - height(x, z - e)) / (2 * e);
        const l = Math.hypot(-dx, 1, -dz) || 1;
        normals.push(-dx / l, 1 / l, -dz / l);
      }
    }
    for (let j = 0; j < segZ; j++) {
      for (let i = 0; i < segX; i++) {
        const a = j * (segX + 1) + i, b = a + segX + 1;
        indices.push(a, b, a + 1, b, b + 1, a + 1);
      }
    }
    return { positions, normals, indices, mode: "triangles" };
  }

  const intParam = (v, fallback, lo, hi) => Math.round(clamp(num(v, fallback), lo, hi));

  const BUILDERS = {
    box: (p) => meshBox(num(p.width, 1), num(p.height, 1), num(p.depth, 1)),
    sphere: (p) => (p.mode === "lines"
      ? meshSphereLines(num(p.radius, 0.5), intParam(p.segments, 20, 4, 64), intParam(p.rings, 12, 2, 40))
      : meshSphere(num(p.radius, 0.5), intParam(p.segments, 24, 4, 64), intParam(p.rings, 14, 2, 40))),
    cylinder: (p) => {
      const bottom = num(p.radius, 0.4);
      // radiusTop defaults to the bottom radius, so a plain cylinder needs no
      // extra field; setting it smaller gives a truncated cone (a taper, a
      // Venturi, a slump cone) and zero gives a point.
      return meshCylinder(num(p.radiusTop, bottom), bottom, num(p.height, 1), intParam(p.segments, 24, 4, 64));
    },
    cone: (p) => meshCone(num(p.radius, 0.4), num(p.height, 1), intParam(p.segments, 24, 4, 64)),
    torus: (p) => meshTorus(num(p.radius, 0.6), num(p.tube, 0.15), intParam(p.segments, 32, 4, 96), intParam(p.rings, 16, 3, 48)),
    plane: (p) => meshPlane(num(p.size, 2)),
    grid: (p) => meshGrid(num(p.size, 4), intParam(p.divisions, 10, 2, 40)),
    axes: (p) => meshAxes(num(p.length, 1)),
    line: (p) => meshPolyline(vecList(p.points, 2)),
    points: (p) => meshPoints(vecList(p.points, 1)),
    arrow: (p) => meshArrow(vec3(p.from), vec3(p.to), num(p.shaft, 0.03), num(p.headLength, 0.22), num(p.headRadius, 0.09)),
    tube: (p) => meshTube(vecList(p.points, 2), num(p.radius, 0.05), 12),
    helix: (p) => meshTube(
      helixPoints(num(p.radius, 0.5), num(p.height, 1), num(p.turns, 4), intParam(p.samples, 96, 8, 400)),
      num(p.tube, 0.045), 12,
    ),
    wave: (p) => meshWave(num(p.width, 2), num(p.depth, 2), intParam(p.segmentsX, 32, 2, 96), intParam(p.segmentsZ, 32, 2, 96), num(p.amplitude, 0.25), num(p.frequency, 3)),
  };

  function vec3(v, fallback = 0) {
    return [num(v && v[0], fallback), num(v && v[1], fallback), num(v && v[2], fallback)];
  }

  function vecList(list, min) {
    if (!Array.isArray(list)) return [];
    const out = [];
    for (const item of list) {
      if (Array.isArray(item) && item.length >= 3 && item.slice(0, 3).every((n) => Number.isFinite(+n))) {
        out.push([+item[0], +item[1], +item[2]]);
      }
      if (out.length >= MAX_POINTS) break;
    }
    return out.length >= min ? out : [];
  }

  function parseColor(value, fallback) {
    if (Array.isArray(value) && value.length >= 3 && value.slice(0, 3).every((n) => Number.isFinite(+n))) {
      return value.slice(0, 3).map((n) => clamp(+n, 0, 1));
    }
    if (typeof value === "string") {
      const m = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.exec(value.trim());
      if (m) {
        let hex = m[1];
        if (hex.length === 3) hex = hex.split("").map((c) => c + c).join("");
        return [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
      }
    }
    return fallback || [0.55, 0.65, 0.95];
  }

  /* -------------------------------------------------------------------- GL -- */

  const VERT = `
    attribute vec3 aPosition;
    attribute vec3 aNormal;
    uniform mat4 uModel, uView, uProj;
    uniform mat3 uNormalMat;
    varying vec3 vNormal;
    varying vec3 vWorld;
    void main() {
      vec4 world = uModel * vec4(aPosition, 1.0);
      vWorld = world.xyz;
      vNormal = normalize(uNormalMat * aNormal);
      gl_Position = uProj * uView * world;
      gl_PointSize = 5.0;
    }`;

  const FRAG = `
    precision mediump float;
    varying vec3 vNormal;
    varying vec3 vWorld;
    uniform vec3 uColor, uLightDir, uFillDir, uEye;
    uniform float uAmbient, uOpacity, uUnlit;
    void main() {
      if (uUnlit > 0.5) { gl_FragColor = vec4(uColor, uOpacity); return; }
      vec3 n = normalize(vNormal);
      float key = max(dot(n, normalize(uLightDir)), 0.0);
      float fill = max(dot(n, normalize(uFillDir)), 0.0) * 0.35;
      vec3 h = normalize(normalize(uLightDir) + normalize(uEye - vWorld));
      float spec = pow(max(dot(n, h), 0.0), 32.0) * 0.4;
      vec3 c = uColor * (uAmbient + key + fill) + vec3(spec);
      gl_FragColor = vec4(clamp(c, 0.0, 1.0), uOpacity);
    }`;

  const UNIFORMS = ["uModel", "uView", "uProj", "uNormalMat", "uColor", "uLightDir", "uFillDir", "uEye", "uAmbient", "uOpacity", "uUnlit"];

  function compile(gl, type, src) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, src);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      const log = gl.getShaderInfoLog(shader);
      gl.deleteShader(shader);
      throw new Error("shader compile failed: " + log);
    }
    return shader;
  }

  /* ----------------------------------------------------------------- view --- */

  class View3D {
    constructor(container, scene) {
      this.container = container;
      this.scene = scene;
      this.canvas = container.querySelector("canvas");
      this.labelLayer = container.querySelector(".ev3d-labels");
      const cam = scene.camera || {};
      this.home = {
        yaw: num(cam.yaw, 35) * DEG,
        pitch: clamp(num(cam.pitch, 18) * DEG, -1.5, 1.5),
        distance: clamp(num(cam.distance, 6), 0.8, 200),
      };
      this.yaw = this.home.yaw;
      this.pitch = this.home.pitch;
      this.distance = this.home.distance;
      this.fov = clamp(num(cam.fov, 45), 15, 100) * DEG;
      this.spin = REDUCED ? 0 : num(scene.spin, 0.22);
      this.ambient = clamp(num(scene.ambient, 0.28), 0, 1);
      this.target = vec3(scene.target, 0);
      this.background = typeof scene.background === "string" ? scene.background : null;
      this.visible = true;
      this.dirty = true;
      this.engaged = false;
      this.cssWidth = 1;
      this.cssHeight = 1;
      this.objects = [];
      this.labels = [];
      this.last = 0;
    }

    init() {
      const gl = this.canvas.getContext("webgl", { antialias: true, alpha: false })
        || this.canvas.getContext("experimental-webgl");
      if (!gl) return false;
      this.gl = gl;
      this.program = gl.createProgram();
      gl.attachShader(this.program, compile(gl, gl.VERTEX_SHADER, VERT));
      gl.attachShader(this.program, compile(gl, gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(this.program);
      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) return false;
      gl.useProgram(this.program);

      this.u = {};
      UNIFORMS.forEach((name) => { this.u[name] = gl.getUniformLocation(this.program, name); });
      this.aPosition = gl.getAttribLocation(this.program, "aPosition");
      this.aNormal = gl.getAttribLocation(this.program, "aNormal");
      gl.enableVertexAttribArray(this.aPosition);
      if (this.aNormal >= 0) gl.enableVertexAttribArray(this.aNormal);

      gl.enable(gl.DEPTH_TEST);
      gl.enable(gl.CULL_FACE);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      this.buildObjects();
      this.buildLabels();
      this.bindControls();
      this.resize();
      return this.objects.length > 0;
    }

    buildObjects() {
      const gl = this.gl;
      (this.scene.objects || []).slice(0, 220).forEach((spec) => {
        const builder = BUILDERS[spec && spec.mesh];
        if (!builder) return;
        let mesh;
        try { mesh = builder(spec); } catch (_) { return; }
        if (!mesh || !mesh.positions.length || mesh.positions.length / 3 > MAX_VERTS) return;

        const interleaved = new Float32Array(mesh.positions.length * 2);
        for (let i = 0, j = 0; i < mesh.positions.length; i += 3, j += 6) {
          interleaved[j] = mesh.positions[i];
          interleaved[j + 1] = mesh.positions[i + 1];
          interleaved[j + 2] = mesh.positions[i + 2];
          interleaved[j + 3] = mesh.normals[i] || 0;
          interleaved[j + 4] = mesh.normals[i + 1] || 0;
          interleaved[j + 5] = mesh.normals[i + 2] || 1;
        }
        const vertexBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
        gl.bufferData(gl.ARRAY_BUFFER, interleaved, gl.STATIC_DRAW);
        const indexBuffer = gl.createBuffer();
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(mesh.indices), gl.STATIC_DRAW);

        const scale = Array.isArray(spec.scale) ? vec3(spec.scale, 1) : [num(spec.scale, 1), num(spec.scale, 1), num(spec.scale, 1)];
        this.objects.push({
          vertexBuffer,
          indexBuffer,
          count: mesh.indices.length,
          mode: mesh.mode === "lines" ? gl.LINES : mesh.mode === "points" ? gl.POINTS : gl.TRIANGLES,
          color: parseColor(spec.color),
          opacity: clamp(num(spec.opacity, 1), 0.05, 1),
          unlit: mesh.mode !== "triangles" || spec.unlit === true ? 1 : 0,
          position: vec3(spec.position, 0),
          rotation: vec3(spec.rotation, 0),
          scale,
        });
      });
      // Opaque geometry first, translucent last, so blending reads correctly.
      this.objects.sort((a, b) => b.opacity - a.opacity);
    }

    buildLabels() {
      if (!this.labelLayer) return;
      this.labelLayer.textContent = "";
      (this.scene.labels || []).slice(0, 40).forEach((label) => {
        const text = String(label && label.text ? label.text : "").slice(0, 60);
        if (!text) return;
        const el = document.createElement("span");
        el.className = "ev3d-label";
        el.textContent = text;
        this.labelLayer.appendChild(el);
        this.labels.push({ el, at: vec3(label.at, 0) });
      });
    }

    bindControls() {
      const el = this.canvas;
      let dragging = false, lastX = 0, lastY = 0, pinch = 0;

      el.addEventListener("pointerdown", (e) => {
        dragging = true;
        this.engaged = true;
        lastX = e.clientX;
        lastY = e.clientY;
        el.classList.add("ev3d-dragging");
        try { el.setPointerCapture(e.pointerId); } catch (_) { /* unsupported */ }
        if (el.focus) el.focus({ preventScroll: true });
      });
      el.addEventListener("pointermove", (e) => {
        if (!dragging) return;
        this.yaw += (e.clientX - lastX) * 0.008;
        this.pitch = clamp(this.pitch + (e.clientY - lastY) * 0.008, -1.5, 1.5);
        lastX = e.clientX;
        lastY = e.clientY;
        this.spin = 0;          // taking manual control stops the auto-spin
        this.dirty = true;
      });
      const release = (e) => {
        dragging = false;
        el.classList.remove("ev3d-dragging");
        try { el.releasePointerCapture(e.pointerId); } catch (_) { /* already released */ }
      };
      el.addEventListener("pointerup", release);
      el.addEventListener("pointercancel", release);
      el.addEventListener("pointerleave", () => { this.engaged = false; });
      el.addEventListener("blur", () => { this.engaged = false; });

      // Zoom only once the model is engaged, so scrolling past a model on a
      // long notes page still scrolls the page instead of the camera.
      el.addEventListener("wheel", (e) => {
        if (!this.engaged) return;
        e.preventDefault();
        this.distance = clamp(this.distance * (1 + Math.sign(e.deltaY) * 0.12), 0.8, 200);
        this.dirty = true;
      }, { passive: false });

      el.addEventListener("touchmove", (e) => {
        if (e.touches.length !== 2) return;
        const span = Math.hypot(e.touches[0].clientX - e.touches[1].clientX, e.touches[0].clientY - e.touches[1].clientY);
        if (pinch) {
          this.distance = clamp(this.distance * (pinch / (span || pinch)), 0.8, 200);
          this.dirty = true;
        }
        pinch = span;
      }, { passive: true });
      el.addEventListener("touchend", () => { pinch = 0; });

      el.addEventListener("dblclick", () => {
        this.yaw = this.home.yaw;
        this.pitch = this.home.pitch;
        this.distance = this.home.distance;
        this.dirty = true;
      });

      el.addEventListener("keydown", (e) => {
        const step = 0.18;
        if (e.key === "ArrowLeft") this.yaw -= step;
        else if (e.key === "ArrowRight") this.yaw += step;
        else if (e.key === "ArrowUp") this.pitch = clamp(this.pitch + step, -1.5, 1.5);
        else if (e.key === "ArrowDown") this.pitch = clamp(this.pitch - step, -1.5, 1.5);
        else if (e.key === "+" || e.key === "=") this.distance = clamp(this.distance * 0.9, 0.8, 200);
        else if (e.key === "-" || e.key === "_") this.distance = clamp(this.distance * 1.1, 0.8, 200);
        else return;
        e.preventDefault();
        this.spin = 0;
        this.dirty = true;
      });

      if ("IntersectionObserver" in window) {
        this.observer = new IntersectionObserver((entries) => {
          this.visible = entries.some((entry) => entry.isIntersecting);
          if (this.visible) { this.resize(); this.dirty = true; }
        }, { rootMargin: "160px" });
        this.observer.observe(this.container);
      }
      window.addEventListener("resize", () => { this.resize(); this.dirty = true; }, { passive: true });
    }

    resize() {
      const rect = this.container.getBoundingClientRect();
      if (rect.width < 1) return;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.cssWidth = rect.width;
      this.cssHeight = Math.max(rect.height, 1);
      const w = Math.max(1, Math.round(this.cssWidth * dpr));
      const h = Math.max(1, Math.round(this.cssHeight * dpr));
      if (this.canvas.width !== w || this.canvas.height !== h) {
        this.canvas.width = w;
        this.canvas.height = h;
      }
      this.aspect = w / h;
      this.gl.viewport(0, 0, w, h);
    }

    frame(now) {
      if (!this.visible || document.hidden) return;
      const dt = this.last ? Math.min((now - this.last) / 1000, 0.1) : 0;
      this.last = now;
      if (this.spin) {
        this.yaw += this.spin * dt;
        this.dirty = true;
      }
      if (!this.dirty) return;
      this.dirty = this.spin !== 0;

      const gl = this.gl;
      const bg = this.background ? parseColor(this.background, [0.04, 0.07, 0.14]) : [0.04, 0.07, 0.14];
      gl.clearColor(bg[0], bg[1], bg[2], 1);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      const eye = [
        this.target[0] + this.distance * Math.cos(this.pitch) * Math.sin(this.yaw),
        this.target[1] + this.distance * Math.sin(this.pitch),
        this.target[2] + this.distance * Math.cos(this.pitch) * Math.cos(this.yaw),
      ];
      const view = mat4.lookAt(mat4.create(), eye, this.target, [0, 1, 0]);
      const proj = mat4.perspective(mat4.create(), this.fov, this.aspect, 0.05, this.distance * 8 + 20);
      const model = mat4.create();
      const nmat = new Float32Array(9);

      gl.uniformMatrix4fv(this.u.uView, false, view);
      gl.uniformMatrix4fv(this.u.uProj, false, proj);
      gl.uniform3fv(this.u.uEye, eye);
      gl.uniform3fv(this.u.uLightDir, [-0.45, 0.82, 0.55]);
      gl.uniform3fv(this.u.uFillDir, [0.6, -0.2, -0.5]);
      gl.uniform1f(this.u.uAmbient, this.ambient);

      this.objects.forEach((o) => {
        mat4.compose(model, o.position, o.rotation, o.scale);
        mat4.normalMatrix(nmat, model);
        gl.uniformMatrix4fv(this.u.uModel, false, model);
        gl.uniformMatrix3fv(this.u.uNormalMat, false, nmat);
        gl.uniform3fv(this.u.uColor, o.color);
        gl.uniform1f(this.u.uOpacity, o.opacity);
        gl.uniform1f(this.u.uUnlit, o.unlit);
        if (o.opacity < 1) gl.depthMask(false);
        gl.bindBuffer(gl.ARRAY_BUFFER, o.vertexBuffer);
        gl.vertexAttribPointer(this.aPosition, 3, gl.FLOAT, false, 24, 0);
        if (this.aNormal >= 0) gl.vertexAttribPointer(this.aNormal, 3, gl.FLOAT, false, 24, 12);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, o.indexBuffer);
        if (o.mode === gl.TRIANGLES) gl.enable(gl.CULL_FACE); else gl.disable(gl.CULL_FACE);
        gl.drawElements(o.mode, o.count, gl.UNSIGNED_SHORT, 0);
        gl.depthMask(true);
      });
      gl.enable(gl.CULL_FACE);

      this.placeLabels(mat4.multiply(mat4.create(), proj, view));
    }

    placeLabels(viewProjection) {
      const out = [0, 0, 0];
      this.labels.forEach((label) => {
        project(out, viewProjection, label.at);
        if (out[2] <= 0) {
          label.el.style.display = "none";
          return;
        }
        label.el.style.display = "";
        label.el.style.left = ((out[0] * 0.5 + 0.5) * this.cssWidth).toFixed(1) + "px";
        label.el.style.top = ((0.5 - out[1] * 0.5) * this.cssHeight).toFixed(1) + "px";
      });
    }
  }

  /* ----------------------------------------------------------------- boot --- */

  const views = [];
  let raf = 0;

  function tick(now) {
    views.forEach((view) => {
      try { view.frame(now); } catch (_) { /* one bad model must not stop the rest */ }
    });
    raf = window.requestAnimationFrame(tick);
  }

  function fail(container, message) {
    container.classList.add("ev3d-failed");
    const canvas = container.querySelector("canvas");
    if (canvas) canvas.style.display = "none";
    const hint = container.querySelector(".ev3d-hint");
    if (hint) hint.remove();
    const note = document.createElement("p");
    note.className = "ev3d-fallback";
    note.setAttribute("role", "note");
    note.textContent = message;
    container.appendChild(note);
  }

  function mount(container) {
    if (container.dataset.ev3dReady === "1") return;
    container.dataset.ev3dReady = "1";

    let scene = null;
    try { scene = JSON.parse(container.dataset.scene || "null"); } catch (_) { scene = null; }
    if (!scene || !Array.isArray(scene.objects) || !scene.objects.length) {
      fail(container, "This model could not be read.");
      return;
    }

    const view = new View3D(container, scene);
    let ready = false;
    try { ready = view.init(); } catch (_) { ready = false; }
    if (!ready) {
      fail(container, window.WebGLRenderingContext
        ? "This model could not be drawn here."
        : "This browser has no WebGL, so the 3D view is unavailable — the written explanation above covers the same idea.");
      return;
    }
    container.classList.add("ev3d-live");
    views.push(view);
    if (!raf) raf = window.requestAnimationFrame(tick);
  }

  function boot() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-model3d]"), mount);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  // Exposed so a panel added after load can mount its own models, and so
  // scripts/check_engine3d.js can run the mesh maths outside a browser.
  window.EngineVerse3D = { mount, boot, builders: BUILDERS, mat4, project, parseColor, orientAlong };
})();
