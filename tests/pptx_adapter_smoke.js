const pptxgen = require("pptxgenjs");

const output = process.argv[2];
if (!output) throw new Error("Usage: node pptx_adapter_smoke.js <output.pptx>");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "AutoFlow adapter smoke test";
pptx.subject = "External pptx Skill backend verification";
pptx.title = "AutoFlow PPT adapter";
pptx.company = "AutoFlow";
pptx.lang = "zh-CN";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "zh-CN",
};

const C = {
  ink: "172033",
  cream: "F5F1E8",
  orange: "EF6A3A",
  teal: "137C8B",
  white: "FFFFFF",
  muted: "667085",
};

let slide = pptx.addSlide();
slide.background = { color: C.ink };
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 4.7, h: 7.5, fill: { color: C.orange }, line: { color: C.orange } });
slide.addShape(pptx.ShapeType.arc, { x: 8.9, y: -0.7, w: 3.5, h: 3.5, rotate: 25, adjustPoint: 0.25, fill: { color: C.teal, transparency: 8 }, line: { color: C.teal } });
slide.addText("AUTOFLOW", { x: 0.75, y: 0.72, w: 3.1, h: 0.35, margin: 0, fontSize: 13, bold: true, charSpacing: 2.4, color: C.ink });
slide.addText("六个模块，\n一条可验证的流程", { x: 5.25, y: 1.35, w: 6.7, h: 1.85, margin: 0, fontSize: 33, bold: true, color: C.white, breakLine: false });
slide.addText("Agent 负责判断与调用，状态机负责依赖、STOP 和真实产物。", { x: 5.28, y: 3.55, w: 6.55, h: 0.55, margin: 0, fontSize: 16, color: "D4D9E4" });
slide.addText("PPT ADAPTER SMOKE TEST", { x: 5.28, y: 6.55, w: 4.5, h: 0.3, margin: 0, fontSize: 10, bold: true, charSpacing: 1.4, color: C.orange });

slide = pptx.addSlide();
slide.background = { color: C.cream };
slide.addText("组合，而不是固定流水线", { x: 0.7, y: 0.55, w: 8.6, h: 0.65, margin: 0, fontSize: 28, bold: true, color: C.ink });
slide.addText("每个模块只承诺清晰的输入、输出与验证。", { x: 0.72, y: 1.28, w: 6.8, h: 0.35, margin: 0, fontSize: 13, color: C.muted });

const modules = [
  ["TASK", "research · build · compute · execute", C.orange],
  ["IMAGE", "capture · ai · diagram · chart", C.teal],
  ["WORD", "create · edit · fill", "B7791F"],
  ["PPT", "external Skill adapter", "7C3AED"],
  ["VIDEO", "analyze · record · create · process", "2563EB"],
  ["PACKAGE", "declared artifacts only", "059669"],
];
modules.forEach((item, index) => {
  const col = index % 3;
  const row = Math.floor(index / 3);
  const x = 0.72 + col * 4.14;
  const y = 2.0 + row * 2.16;
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 3.75, h: 1.72, fill: { color: C.white }, line: { color: "DDD7CA", width: 1 } });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.1, h: 1.72, fill: { color: item[2] }, line: { color: item[2] } });
  slide.addText(item[0], { x: x + 0.32, y: y + 0.32, w: 2.9, h: 0.35, margin: 0, fontSize: 18, bold: true, color: C.ink });
  slide.addText(item[1], { x: x + 0.32, y: y + 0.92, w: 3.05, h: 0.42, margin: 0, fontSize: 11, color: C.muted });
});
slide.addText("PLAN  →  SOURCE  →  VISUAL  →  DELIVERY", { x: 0.72, y: 6.72, w: 8.5, h: 0.3, margin: 0, fontSize: 11, bold: true, charSpacing: 1.1, color: C.orange });

pptx.writeFile({ fileName: output });
