/**
 * table-tool / engine.js
 * 纯函数引擎：合表、清洗、去重、汇总、导出 CSV。
 * 无依赖，浏览器与 Node 均可运行（Node 里走 module.exports）。
 */

/** 表头归一：去 BOM、去首尾空白、压缩内部空白 */
function normalizeHeader(h) {
  return String(h == null ? "" : h)
    .replace(/^\uFEFF/, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** 单元格清洗：字符串去首尾空白、压缩内部空白、全角空格转半角空白；空串归 "" */
function cleanCell(v) {
  if (v == null) return "";
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v;
  if (v instanceof Date) return v.toISOString().slice(0, 10);
  let s = String(v).replace(/\u3000/g, " ").replace(/\s+/g, " ").trim();
  return s;
}

/** 尝试把"看起来是数字"的字符串转成数字（去千分位、去货币符号、去百分号保留数值） */
function coerceNumber(v) {
  if (typeof v === "number") return v;
  if (typeof v !== "string") return v;
  const s = v.trim();
  if (s === "") return v;
  const m = s.match(/^-?[$€£¥]?\s*-?[\d,]+(\.\d+)?%?$/);
  if (!m) return v;
  const isPct = s.endsWith("%");
  const num = Number(s.replace(/[$€£¥,\s%]/g, ""));
  if (!isFinite(num)) return v;
  return isPct ? num / 100 : num;
}

/** 把多张表合并成一张：列名按"首次出现顺序"取并集，缺列补 ""
 *  同时检测"字段数不匹配"的行（真实数据最常见的错位病）并回报 warnings
 */
function mergeTables(tables) {
  const headers = [];
  const seen = new Set();
  for (const t of tables) {
    for (const raw of t.headers || []) {
      const h = normalizeHeader(raw);
      if (h === "") continue;
      if (!seen.has(h)) { seen.add(h); headers.push(h); }
    }
  }
  const rows = [];
  const warnings = [];
  for (const t of tables) {
    const hs = (t.headers || []).map(normalizeHeader);
    const all = t.rows || [];
    for (let ri = 0; ri < all.length; ri++) {
      const r = all[ri];
      // 字段数不匹配 ⇒ 记警告（不去改数据，只报告）
      if (r.length !== hs.length) {
        warnings.push({
          file: t.name || "(未命名)",
          row: ri + 2,               // +1 表头，+1 转成人类行号
          got: r.length,
          expect: hs.length,
        });
      }
      const out = new Array(headers.length).fill("");
      for (let i = 0; i < hs.length; i++) {
        const idx = headers.indexOf(hs[i]);
        if (idx >= 0) out[idx] = cleanCell(r[i]);
      }
      rows.push(out);
    }
  }
  return { headers, rows, warnings };
}

/** 清洗整表：逐格 cleanCell；可选把数字型列转成数字 */
function cleanTable(table, opts = {}) {
  const headers = table.headers.map(normalizeHeader);
  const rows = table.rows.map((r) =>
    r.map((c) => {
      const cleaned = cleanCell(c);
      return opts.coerceNumbers ? coerceNumber(cleaned) : cleaned;
    })
  );
  return { headers, rows };
}

/** 去重：keys 为空则按整行；否则按指定列名组合 */
function dedupeRows(table, keys = []) {
  const idxs = keys.length
    ? keys.map((k) => table.headers.indexOf(normalizeHeader(k)))
    : table.headers.map((_, i) => i);
  const seen = new Set();
  const rows = [];
  let removed = 0;
  for (const r of table.rows) {
    const sig = JSON.stringify(idxs.map((i) => (i >= 0 ? r[i] : undefined)));
    if (seen.has(sig)) { removed++; continue; }
    seen.add(sig);
    rows.push(r);
  }
  return { table: { headers: table.headers, rows }, removed };
}

/** 去掉完全为空的行 */
function dropEmptyRows(table) {
  const rows = table.rows.filter((r) => r.some((c) => cleanCell(c) !== ""));
  return { table: { headers: table.headers, rows }, removed: table.rows.length - rows.length };
}

/**
 * 分组汇总
 * @param {string} groupBy 分组列名
 * @param {Array<{column:string, op:"count"|"sum"|"avg"|"min"|"max"}>} aggs
 */
function pivot(table, groupBy, aggs) {
  const gi = table.headers.indexOf(normalizeHeader(groupBy));
  if (gi < 0) throw new Error("找不到分组列: " + groupBy);
  const buckets = new Map();
  for (const r of table.rows) {
    const k = String(r[gi]);
    if (!buckets.has(k)) buckets.set(k, []);
    buckets.get(k).push(r);
  }
  const headers = [groupBy, ...aggs.map((a) => a.op + "(" + a.column + ")")];
  const rows = [];
  for (const [k, rs] of buckets) {
    const out = [k];
    for (const a of aggs) {
      const ci = table.headers.indexOf(normalizeHeader(a.column));
      const nums = rs.map((r) => Number(coerceNumber(r[ci]))).filter((n) => isFinite(n));
      if (a.op === "count") out.push(rs.length);
      else if (a.op === "sum") out.push(nums.reduce((x, y) => x + y, 0));
      else if (a.op === "avg") out.push(nums.length ? nums.reduce((x, y) => x + y, 0) / nums.length : "");
      else if (a.op === "min") out.push(nums.length ? Math.min(...nums) : "");
      else if (a.op === "max") out.push(nums.length ? Math.max(...nums) : "");
      else throw new Error("未知聚合: " + a.op);
    }
    rows.push(out);
  }
  return { headers, rows };
}

/** 转 CSV（带转义） */
function toCSV(table) {
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lines = [table.headers.map(esc).join(",")];
  for (const r of table.rows) lines.push(r.map(esc).join(","));
  return lines.join("\n");
}

/** 从 CSV 文本读表（简单可靠版：不依赖库） */
function parseCSV(text) {
  const rows = [];
  let row = [], cell = "", inQ = false;
  const s = String(text).replace(/^\uFEFF/, "");
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (inQ) {
      if (ch === '"') {
        if (s[i + 1] === '"') { cell += '"'; i++; }
        else inQ = false;
      } else cell += ch;
    } else {
      if (ch === '"') inQ = true;
      else if (ch === ",") { row.push(cell); cell = ""; }
      else if (ch === "\n") { row.push(cell); rows.push(row); row = []; cell = ""; }
      else if (ch === "\r") { /* skip */ }
      else cell += ch;
    }
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  const header = rows.shift() || [];
  return { headers: header.map(normalizeHeader), rows };
}

/* 浏览器：挂到 window.TableEngine —— index.html 直接用它 */
if (typeof window !== "undefined") {
  window.TableEngine = {
    normalizeHeader, cleanCell, coerceNumber, mergeTables, cleanTable,
    dedupeRows, dropEmptyRows, pivot, toCSV, parseCSV,
  };
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    normalizeHeader, cleanCell, coerceNumber, mergeTables, cleanTable,
    dedupeRows, dropEmptyRows, pivot, toCSV, parseCSV,
  };
}
