'use strict';

// figma-squircle v1.1.0 — browser port
// Generates Figma-flavored SVG squircle paths (continuous corner smoothing)
// https://github.com/phamfoo/figma-squircle
//
// API: getSvgPath({ width, height, cornerRadius, cornerSmoothing, preserveSmoothing })
// Returns SVG path `d` attribute string in pixel coordinates.
//
// Integration:
//   1. Include this script in your page
//   2. After rendering cards, call applySquircles() to generate per-card SVG clip paths
//   3. Use clip-path: url(#sq-dyn-{idx}) in CSS (applied automatically)

(function(global) {
  function toRadians(d) { return d * Math.PI / 180; }

  // ── Math: distribute corner radius budgets ──
  var adjacentsByCorner = {
    topLeft: [{ corner: 'topRight', side: 'top' }, { corner: 'bottomLeft', side: 'left' }],
    topRight: [{ corner: 'topLeft', side: 'top' }, { corner: 'bottomRight', side: 'right' }],
    bottomLeft: [{ corner: 'bottomRight', side: 'bottom' }, { corner: 'topLeft', side: 'left' }],
    bottomRight: [{ corner: 'bottomLeft', side: 'bottom' }, { corner: 'topRight', side: 'right' }]
  };

  function distributeAndNormalize(opts) {
    var budgetMap = { topLeft: -1, topRight: -1, bottomLeft: -1, bottomRight: -1 };
    var radiusMap = {
      topLeft: opts.topLeftCornerRadius,
      topRight: opts.topRightCornerRadius,
      bottomLeft: opts.bottomLeftCornerRadius,
      bottomRight: opts.bottomRightCornerRadius
    };
    Object.entries(radiusMap).sort(function(a, b) { return b[1] - a[1]; }).forEach(function(entry) {
      var corner = entry[0], radius = entry[1];
      var budget = Infinity;
      adjacentsByCorner[corner].forEach(function(adj) {
        var adjRadius = radiusMap[adj.corner];
        if (radius === 0 && adjRadius === 0) { budget = Math.min(budget, 0); return; }
        var adjBudget = budgetMap[adj.corner];
        var sideLen = adj.side === 'top' || adj.side === 'bottom' ? opts.width : opts.height;
        if (adjBudget >= 0) {
          budget = Math.min(budget, sideLen - budgetMap[adj.corner]);
        } else {
          budget = Math.min(budget, radius / (radius + adjRadius) * sideLen);
        }
      });
      budgetMap[corner] = budget;
      radiusMap[corner] = Math.min(radius, budget);
    });
    var r = function(c) { return { radius: radiusMap[c], roundingAndSmoothingBudget: budgetMap[c] }; };
    return { topLeft: r('topLeft'), topRight: r('topRight'), bottomLeft: r('bottomLeft'), bottomRight: r('bottomRight') };
  }

  // ── Math: compute corner path parameters ──
  function getPathParamsForCorner(opts) {
    var cr = opts.cornerRadius, cs = opts.cornerSmoothing;
    var p = (1 + cs) * cr;
    if (!opts.preserveSmoothing) {
      var maxCS = opts.roundingAndSmoothingBudget / cr - 1;
      cs = Math.min(cs, maxCS);
      p = Math.min(p, opts.roundingAndSmoothingBudget);
    }
    var arcMeasure = 90 * (1 - cs);
    var arcSectionLength = Math.sin(toRadians(arcMeasure / 2)) * cr * Math.SQRT2;
    var angleAlpha = (90 - arcMeasure) / 2;
    var p3ToP4Dist = cr * Math.tan(toRadians(angleAlpha / 2));
    var angleBeta = 45 * cs;
    var c = p3ToP4Dist * Math.cos(toRadians(angleBeta));
    var d = c * Math.tan(toRadians(angleBeta));
    var b = (p - arcSectionLength - c - d) / 3;
    var a = 2 * b;
    if (opts.preserveSmoothing && p > opts.roundingAndSmoothingBudget) {
      var p1ToP3Max = opts.roundingAndSmoothingBudget - d - arcSectionLength - c;
      var minA = p1ToP3Max / 6, maxB = p1ToP3Max - minA;
      b = Math.min(b, maxB); a = p1ToP3Max - b;
      p = Math.min(p, opts.roundingAndSmoothingBudget);
    }
    return { a: a, b: b, c: c, d: d, p: p, arcSectionLength: arcSectionLength, cornerRadius: cr };
  }

  // ── SVG path generation ──
  function f4(x) { return x.toFixed(4); }

  function drawCorner(pp, corner) {
    if (!pp.cornerRadius) return 'l ' + f4(pp.p) + ' 0';
    var cr = pp.cornerRadius, a = pp.a, b = pp.b, c = pp.c, d = pp.d, arc = pp.arcSectionLength;
    var ab = a + b, abc = a + b + c, bc = b + c;
    switch (corner) {
      case 'topRight':
        return 'c ' + f4(a) + ' 0 ' + f4(ab) + ' 0 ' + f4(abc) + ' ' + f4(d) +
          ' a ' + f4(cr) + ' ' + f4(cr) + ' 0 0 1 ' + f4(arc) + ' ' + f4(arc) +
          ' c ' + f4(d) + ' ' + f4(c) + ' ' + f4(d) + ' ' + f4(bc) + ' ' + f4(d) + ' ' + f4(abc);
      case 'bottomRight':
        return 'c 0 ' + f4(a) + ' 0 ' + f4(ab) + ' ' + f4(-d) + ' ' + f4(abc) +
          ' a ' + f4(cr) + ' ' + f4(cr) + ' 0 0 1 ' + f4(-arc) + ' ' + f4(arc) +
          ' c ' + f4(-c) + ' ' + f4(d) + ' ' + f4(-bc) + ' ' + f4(d) + ' ' + f4(-abc) + ' ' + f4(d);
      case 'bottomLeft':
        return 'c ' + f4(-a) + ' 0 ' + f4(-ab) + ' 0 ' + f4(-abc) + ' ' + f4(-d) +
          ' a ' + f4(cr) + ' ' + f4(cr) + ' 0 0 1 ' + f4(-arc) + ' ' + f4(-arc) +
          ' c ' + f4(-d) + ' ' + f4(-c) + ' ' + f4(-d) + ' ' + f4(-bc) + ' ' + f4(-d) + ' ' + f4(-abc);
      case 'topLeft':
        return 'c 0 ' + f4(-a) + ' 0 ' + f4(-ab) + ' ' + f4(d) + ' ' + f4(-abc) +
          ' a ' + f4(cr) + ' ' + f4(cr) + ' 0 0 1 ' + f4(arc) + ' ' + f4(-arc) +
          ' c ' + f4(c) + ' ' + f4(-d) + ' ' + f4(bc) + ' ' + f4(-d) + ' ' + f4(abc) + ' ' + f4(-d);
    }
  }

  function getSVGPathFromPathParams(p) {
    var tr = drawCorner(p.topRightPathParams, 'topRight');
    var br = drawCorner(p.bottomRightPathParams, 'bottomRight');
    var bl = drawCorner(p.bottomLeftPathParams, 'bottomLeft');
    var tl = drawCorner(p.topLeftPathParams, 'topLeft');
    return ('M ' + f4(p.width - p.topRightPathParams.p) + ' 0 ' + tr +
      ' L ' + f4(p.width) + ' ' + f4(p.height - p.bottomRightPathParams.p) + ' ' + br +
      ' L ' + f4(p.bottomLeftPathParams.p) + ' ' + f4(p.height) + ' ' + bl +
      ' L 0 ' + f4(p.topLeftPathParams.p) + ' ' + tl + ' Z')
      .replace(/\s+/g, ' ').trim();
  }

  // ── Public API ──
  function getSvgPath(opts) {
    var cornerRadius = opts.cornerRadius || 0;
    var tl = opts.topLeftCornerRadius ?? cornerRadius;
    var tr = opts.topRightCornerRadius ?? cornerRadius;
    var bl = opts.bottomLeftCornerRadius ?? cornerRadius;
    var br = opts.bottomRightCornerRadius ?? cornerRadius;
    var w = opts.width, h = opts.height, cs = opts.cornerSmoothing, pr = opts.preserveSmoothing || false;

    if (tl === tr && tr === br && br === bl) {
      var budget = Math.min(w, h) / 2;
      var cr2 = Math.min(tl, budget);
      var pp = getPathParamsForCorner({ cornerRadius: cr2, cornerSmoothing: cs, preserveSmoothing: pr, roundingAndSmoothingBudget: budget });
      return getSVGPathFromPathParams({ width: w, height: h, topLeftPathParams: pp, topRightPathParams: pp, bottomLeftPathParams: pp, bottomRightPathParams: pp });
    }
    var dist = distributeAndNormalize({ topLeftCornerRadius: tl, topRightCornerRadius: tr, bottomRightCornerRadius: br, bottomLeftCornerRadius: bl, width: w, height: h });
    var mk = function(d) { return getPathParamsForCorner({ cornerRadius: d.radius, cornerSmoothing: cs, preserveSmoothing: pr, roundingAndSmoothingBudget: d.roundingAndSmoothingBudget }); };
    return getSVGPathFromPathParams({ width: w, height: h, topLeftPathParams: mk(dist.topLeft), topRightPathParams: mk(dist.topRight), bottomLeftPathParams: mk(dist.bottomLeft), bottomRightPathParams: mk(dist.bottomRight) });
  }

  // ── Apply to page ──
  var sqResizeTimer = null;

  function applySquircles() {
    var cards = document.querySelectorAll('.node-card, .stat-card, .metric-card, .skeleton-card, .sysinfo-card, .tags-card, .chart-card');
    if (!cards.length) return;

    var defs = document.querySelector('svg#sq-defs defs');
    if (!defs) {
      var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.id = 'sq-defs'; svg.style.cssText = 'position:absolute;width:0;height:0'; svg.setAttribute('aria-hidden', 'true');
      defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
      svg.appendChild(defs);
      document.body.prepend(svg);
    }

    var existing = defs.querySelectorAll('[id^="sq-dyn-"]');
    for (var i = 0; i < existing.length; i++) defs.removeChild(existing[i]);

    cards.forEach(function(card, idx) {
      var w = card.offsetWidth, h = card.offsetHeight;
      if (!w || !h) return;
      var isBig = card.classList.contains('node-card') || card.classList.contains('chart-card') || card.classList.contains('skeleton-card');
      var rad = isBig ? 16 : 12;
      var path = getSvgPath({ width: w, height: h, cornerRadius: rad, cornerSmoothing: 1 });

      var id = 'sq-dyn-' + idx;
      var clip = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
      clip.id = id; clip.setAttribute('clipPathUnits', 'userSpaceOnUse');
      var pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      pathEl.setAttribute('d', path);
      clip.appendChild(pathEl);
      defs.appendChild(clip);
      card.style.clipPath = 'url(#' + id + ')';
    });
  }

  function onResize() {
    if (sqResizeTimer) clearTimeout(sqResizeTimer);
    sqResizeTimer = setTimeout(applySquircles, 150);
  }
  if (window.addEventListener) window.addEventListener('resize', onResize);

  global.getSvgPath = getSvgPath;
  global.applySquircles = applySquircles;
})(window);
