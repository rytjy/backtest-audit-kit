/**
 * build.js —— 把 index.html + engine.js + SheetJS 打成一个单文件 HTML
 * 产物：dist/表格整理工具.html（双击即用，不联网、不上传）
 */
const fs = require("fs");
const path = require("path");

const root = __dirname;
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const engine = fs.readFileSync(path.join(root, "engine.js"), "utf8");
const sheetjsPath = process.env.SHEETJS || "/tmp/xlsx.full.min.js";
let sheetjs = "";
try { sheetjs = fs.readFileSync(sheetjsPath, "utf8"); }
catch (e) { console.log("⚠️ 未找到 SheetJS（" + sheetjsPath + "），将打成 CSV-only 版本"); }

const TAG_ENGINE = '<script src="./engine.js"></script>';
const TAG_CDN = '<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>';

if (!html.includes(TAG_ENGINE)) throw new Error("找不到 engine.js 的 script 标签");
if (!html.includes(TAG_CDN)) throw new Error("找不到 SheetJS CDN 标签");

// ⚠️ 必须用「函数替换」：字符串替换会把内联代码里的 $& / $' 当成替换模式，
// 导致被替换的标签又被原样插回（SheetJS 压缩码里含 $&）
let out = html.replace(TAG_ENGINE, () => "<script>\n" + engine + "\n</script>");
out = out.replace(TAG_CDN, () => sheetjs
  ? "<script>\n" + sheetjs + "\n</script>"
  : "<!-- 离线单文件版：未内联 SheetJS，只支持 CSV（请先另存为 CSV） -->");

// 单文件版标题标记
out = out.replace("<title>表格批量整理工具 · 合并 / 清洗 / 去重 / 汇总</title>",
  "<title>表格整理工具（单文件离线版）· 合并 / 清洗 / 去重 / 汇总</title>");

const distDir = path.join(root, "dist");
fs.mkdirSync(distDir, { recursive: true });
const outPath = path.join(distDir, "表格整理工具.html");
fs.writeFileSync(outPath, out, "utf8");

// 自检
const problems = [];
if (out.includes(TAG_ENGINE)) problems.push("engine 标签未被替换");
if (out.includes(TAG_CDN)) problems.push("CDN 标签未被替换");
if (!out.includes("function mergeTables")) problems.push("引擎函数缺失");
if (sheetjs && !out.includes("XLSX")) problems.push("SheetJS 未内联");
if (/<script src="https?:/.test(out)) problems.push("仍有外部脚本引用（非离线）");

console.log("产物: " + outPath);
console.log("大小: " + (fs.statSync(outPath).size / 1024 / 1024).toFixed(2) + " MB");
console.log("SheetJS 内联: " + (sheetjs ? "是（" + (sheetjs.length / 1024).toFixed(0) + " KB）" : "否（CSV-only）"));
console.log(problems.length ? "❌ 自检未过: " + problems.join(" / ") : "✅ 自检通过：无外部依赖、引擎与解析器均已内联");
process.exitCode = problems.length ? 1 : 0;
