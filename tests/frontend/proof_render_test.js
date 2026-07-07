// esc()/proof-tree render regression harness (design §8):
// loads the real page script with DOM stubs, renders a REAL proof term
// captured from the live API, and asserts escaping is intact.
"use strict";
const fs = require("fs");
const path = require("path");

// --- minimal DOM stubs so top-level startChat()/loadMunicipalities() run ---
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
// strict-mode indirect eval does not create global function bindings --
// strip the pragma (harness only; the real page keeps it)
script = script.replace(/^"use strict";/, "");
(0, eval)(script);  // sloppy indirect eval -> function decls become globals

let failures = 0;
function check(name, cond) {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}`);
  if (!cond) failures++;
}

// --- 1. esc() unit checks (attribute-context safety) ---
check("esc escapes angle brackets", esc("<b>x</b>") === "&lt;b&gt;x&lt;/b&gt;");
check("esc escapes double quotes", esc('a"b') === "a&quot;b");
check("esc escapes single quotes", esc("a'b") === "a&#39;b");
check("esc escapes ampersand", esc("a&b") === "a&amp;b");
check("esc passes Japanese through", esc("児童手当") === "児童手当");

// --- 2. real proof term renders with comparisons escaped ---
const body = JSON.parse(fs.readFileSync(path.join(dir, "proof.json"), "utf-8"));
check("captured proof is a node(...) term", body.proof.startsWith("node("));
const html = renderProof(parseTerm(body.proof));
check("proof renders non-empty", html.includes("<li>"));
// the proof of an age-conditioned program always contains =< or < builtins;
// they must appear entity-escaped, never as raw < in the HTML
const hasComparison = /=<|<|>=/.test(body.proof);
check("captured proof contains a comparison operator", hasComparison);
check("comparison rendered as entity", /&lt;|&gt;/.test(html));
// every raw '<' in the output must start an allowed tag
const rawTags = html.match(/<\/?[^>]*>/g) || [];
const allowed = /^<\/?(li|ul|strong|code|div)( class="[^"]*")?>$/;
const badTags = rawTags.filter(t => !allowed.test(t));
check(`only whitelisted tags in output (bad: ${JSON.stringify(badTags.slice(0,3))})`,
      badTags.length === 0);
// no unescaped fragment of a Prolog comparison survives outside <code> content
check("no raw '=<' outside entities", !html.includes("=<"));

process.exit(failures ? 1 : 0);
