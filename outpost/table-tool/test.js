/**
 * table-tool / test.js —— 用 Node 直接跑：node test.js
 * 证明引擎真的能用（不是"看起来能跑"）。
 */
const assert = require("assert");
const E = require("./engine.js");

let n = 0;
function t(name, fn) {
  try { fn(); n++; console.log("  ✅ " + name); }
  catch (e) { console.log("  ❌ " + name + "\n     " + e.message); process.exitCode = 1; }
}
const pad = (s, w) => String(s) + " ".repeat(Math.max(0, w - String(s).length));

console.log("\n=== table-tool 引擎测试 ===\n");

t("表头归一：BOM / 多余空格 / 全角", () => {
  assert.strictEqual(E.normalizeHeader("\uFEFF 客户 名称 "), "客户 名称");
  assert.strictEqual(E.normalizeHeader("A\u3000\u3000B"), "A B");
});

t("单元格清洗：空白压缩 + 全角空格 + 空值", () => {
  assert.strictEqual(E.cleanCell("  张三 \u3000 "), "张三");
  assert.strictEqual(E.cleanCell(null), "");
  assert.strictEqual(E.cleanCell(12.5), 12.5);
});

t("数字识别：千分位 / 货币 / 百分号 / 非数字不动", () => {
  assert.strictEqual(E.coerceNumber("1,234.5"), 1234.5);
  assert.strictEqual(E.coerceNumber("¥1,000"), 1000);
  assert.strictEqual(E.coerceNumber("12%"), 0.12);
  assert.strictEqual(E.coerceNumber("abc"), "abc");
  assert.strictEqual(E.coerceNumber("2026-10-02"), "2026-10-02");
});

t("合表：列名并集按首次出现排序，缺列补空", () => {
  const a = { headers: ["姓名", "金额"], rows: [["张三", 100]] };
  const b = { headers: ["金额", "城市"], rows: [[200, "北京"]] };
  const m = E.mergeTables([a, b]);
  assert.deepStrictEqual(m.headers, ["姓名", "金额", "城市"]);
  assert.deepStrictEqual(m.rows[0], ["张三", 100, ""]);
  assert.deepStrictEqual(m.rows[1], ["", 200, "北京"]);
});

t("合表：表头空格不一致也能对齐", () => {
  const a = { headers: [" 姓名 "], rows: [["李四"]] };
  const b = { headers: ["姓名"], rows: [["王五"]] };
  const m = E.mergeTables([a, b]);
  assert.deepStrictEqual(m.headers, ["姓名"]);
  assert.deepStrictEqual(m.rows, [["李四"], ["王五"]]);
});

t("去重：按整行", () => {
  const tb = { headers: ["a", "b"], rows: [["1", "x"], ["1", "x"], ["2", "y"]] };
  const r = E.dedupeRows(tb);
  assert.strictEqual(r.removed, 1);
  assert.strictEqual(r.table.rows.length, 2);
});

t("去重：按指定列（同人多行只留一行）", () => {
  const tb = { headers: ["姓名", "订单"], rows: [["张三", "A"], ["张三", "B"], ["李四", "C"]] };
  const r = E.dedupeRows(tb, ["姓名"]);
  assert.strictEqual(r.removed, 1);
  assert.deepStrictEqual(r.table.rows.map((x) => x[0]), ["张三", "李四"]);
});

t("去空行", () => {
  const tb = { headers: ["a", "b"], rows: [["1", ""], ["", "  "], ["2", "x"]] };
  const r = E.dropEmptyRows(tb);
  assert.strictEqual(r.removed, 1);
  assert.strictEqual(r.table.rows.length, 2);
});

t("汇总：分组 count / sum / avg", () => {
  const tb = {
    headers: ["城市", "金额"],
    rows: [["北京", "100"], ["北京", "200"], ["上海", "50"]],
  };
  const p = E.pivot(tb, "城市", [
    { column: "金额", op: "count" },
    { column: "金额", op: "sum" },
    { column: "金额", op: "avg" },
  ]);
  assert.deepStrictEqual(p.headers, ["城市", "count(金额)", "sum(金额)", "avg(金额)"]);
  const bj = p.rows.find((r) => r[0] === "北京");
  assert.deepStrictEqual(bj, ["北京", 2, 300, 150]);
});

t("CSV 往返：带逗号/引号/换行的单元格", () => {
  const tb = { headers: ["名称", "备注"], rows: [["A,B", 'say "hi"'], ["C", "x\ny"]] };
  const csv = E.toCSV(tb);
  const back = E.parseCSV(csv);
  assert.deepStrictEqual(back.headers, ["名称", "备注"]);
  assert.deepStrictEqual(back.rows[0], ["A,B", 'say "hi"']);
  assert.deepStrictEqual(back.rows[1], ["C", "x\ny"]);
});

t("端到端：两份脏表 → 合并 → 清洗 → 去空行 → 汇总", () => {
  const f1 = {
    headers: [" 城市 ", "金额", "备注"],
    rows: [[" 北京 ", "1,000 ", "  ok "], ["北京", "2,000", ""], ["", "", ""]],
  };
  const f2 = {
    headers: ["城市", "金额"],
    rows: [["上海", "¥500"], ["北京", "1,000"]],
  };
  let m = E.mergeTables([f1, f2]);
  m = E.cleanTable(m, { coerceNumbers: true });
  m = E.dropEmptyRows(m).table;
  // 注意：按「整行」去重时，第三条北京（备注为空）与前两条并不相同 ⇒ 不应被去掉
  assert.strictEqual(m.rows.length, 4, "去空行后应剩 4 行");
  const p = E.pivot(m, "城市", [{ column: "金额", op: "sum" }, { column: "金额", op: "count" }]);
  assert.deepStrictEqual(p.rows.find((r) => r[0] === "北京"), ["北京", 4000, 3]);
  assert.deepStrictEqual(p.rows.find((r) => r[0] === "上海"), ["上海", 500, 1]);
});

t("端到端补充：改按「城市」列去重 ⇒ 北京塌缩成一条", () => {
  const f1 = { headers: ["城市", "金额"], rows: [["北京", "1,000"], ["北京", "2,000"]] };
  const f2 = { headers: ["城市", "金额"], rows: [["上海", "¥500"], ["北京", "1,000"]] };
  let m = E.cleanTable(E.mergeTables([f1, f2]), { coerceNumbers: true });
  m = E.dedupeRows(m, ["城市"]).table;
  assert.strictEqual(m.rows.length, 2, "按城市去重后应只剩 2 条");
  assert.deepStrictEqual(
    m.rows.map((r) => r[0]).sort(),
    ["北京", "上海"].sort(),
    "应保留北京与上海各一条（用同一排序比较，不断言原始顺序）"
  );
});

t("字段数不匹配 ⇒ 报告 warning（不改数据）", () => {
  const ok = { name: "a.csv", headers: ["城市", "金额", "订单号"], rows: [["北京", "100", "A-1"]] };
  const bad = { name: "c.csv", headers: ["城市", "金额", "订单号", "渠道"], rows: [["上海", "200", "华为商城"]] };
  const m = E.mergeTables([ok, bad]);
  assert.strictEqual(m.warnings.length, 1, "应报出 1 条错位");
  assert.strictEqual(m.warnings[0].file, "c.csv");
  assert.strictEqual(m.warnings[0].got, 3);
  assert.strictEqual(m.warnings[0].expect, 4);
  assert.strictEqual(m.warnings[0].row, 2, "行号应为人类可读的 2（表头是 1）");
  assert.strictEqual(m.rows.length, 2, "错位行仍保留（只报告，不静默删）");
});

t("字段数一致 ⇒ 无 warning", () => {
  const a = { headers: ["x", "y"], rows: [["1", "2"]] };
  assert.strictEqual(E.mergeTables([a]).warnings.length, 0);
});

console.log("\n=== 结果：" + n + " 项通过 ===" + (process.exitCode ? "（有失败）" : "") + "\n");
