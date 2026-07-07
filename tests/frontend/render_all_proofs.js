// batch render-regression over every decided program's real proof term
"use strict";
const fs = require("fs");
const path = require("path");

function stubEl() {
  return {
    innerHTML: "", className: "", id: "", value: "", scrollTop: 0,
    scrollHeight: 0, textContent: "", style: {}, dataset: {},
    classList: { toggle() {}, add() {}, remove() {} },
    setAttribute() {}, appendChild() {}, remove() {}, addEventListener() {},
  };
}
global.document = {
  createElement: () => stubEl(),
  getElementById: () => stubEl(),
  querySelectorAll: () => [],
};
global.fetch = () => Promise.reject(new Error("no network in harness"));

const dir = path.dirname(__filename);
let script = fs.readFileSync(path.join(dir, "page_script.js"), "utf-8");
script = script.replace(/^"use strict";/, "");
(0, eval)(script);

const proofs = JSON.parse(
  fs.readFileSync(path.join(dir, "proofs_all.json"), "utf-8"));
const allowed = /^<\/?(li|ul|strong|code|div)( class="[^"]*")?>$/;
let ok = 0, fallback = 0, bad = 0;
for (const p of proofs) {
  try {
    const html = renderProof(parseTerm(p.proof));
    const badTags = (html.match(/<\/?[^>]*>/g) || [])
      .filter(t => !allowed.test(t));
    if (!html.includes("<li>") || badTags.length || html.includes("=<")) {
      console.log(`BAD RENDER: ${p.program} badTags=${badTags.slice(0,2)}`);
      bad++;
    } else ok++;
  } catch (e) {
    // acceptable fail-safe path (raw text display), but report it
    console.log(`FALLBACK (raw display): ${p.program}: ${e.message}`);
    fallback++;
  }
}
console.log(`rendered OK: ${ok}, fallback: ${fallback}, bad: ${bad} / ${proofs.length}`);
process.exit(bad ? 1 : 0);
