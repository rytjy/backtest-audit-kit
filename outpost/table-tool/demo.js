/**
 * demo.js —— 命令行演示：读多个 CSV → 合并 → 清洗 → 去空行 → 去重 → 分组汇总
 * 用法：node demo.js sample/客户A_订单.csv sample/客户B_订单.csv
 */
const fs = require("fs");
const E = require("./engine.js");

const files = process.argv.slice(2);
if (!files.length) {
  console.log("用法: node demo.js <a.csv> <b.csv> ...");
  process.exit(1);
}

const tables = files.map((f) => {
  const t = E.parseCSV(fs.readFileSync(f, "utf8"));
  console.log("读取 " + f + "  →  " + t.rows.length + " 行 × " + t.headers.length + " 列");
  return t;
});

let merged = E.mergeTables(tables);
merged = E.cleanTable(merged, { coerceNumbers: true });
const dropped = E.dropEmptyRows(merged);
merged = dropped.table;
const dedup = E.dedupeRows(merged);
merged = dedup.table;

console.log("\n—— 合并+清洗后 ——");
console.log("列: " + merged.headers.join(" | "));
merged.rows.forEach((r) => console.log("  " + r.map((c) => String(c)).join(" | ")));
console.log("去掉空行 " + dropped.removed + " 行 · 去掉重复 " + dedup.removed + " 行");

const sumCol = merged.headers.includes("金额") ? "金额" : merged.headers[1];
const byCol = merged.headers[0];
const piv = E.pivot(merged, byCol, [
  { column: sumCol, op: "sum" },
  { column: sumCol, op: "count" },
]);
console.log("\n—— 按「" + byCol + "」汇总 ——");
console.log(piv.headers.join(" | "));
piv.rows.forEach((r) => console.log("  " + r.map((c) => String(c)).join(" | ")));
console.log("\n导出 CSV 前 3 行预览:\n" + E.toCSV(merged).split("\n").slice(0, 3).join("\n"));
