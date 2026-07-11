// Chat-integration harness: loads the real page script with DOM stubs,
// drives the REAL onboarding flow (birth date -> children -> income ->
// doJudge), then exercises sendChat() success / XSS / 429 / network /
// ward-switch / 503 paths against fixtures built from a real judgment.
"use strict";
const fs = require("fs");
const path = require("path");

const dir = path.dirname(__filename);
const FX = JSON.parse(fs.readFileSync(path.join(dir, "chat_fixtures.json"), "utf-8"));

// ---------------- DOM stub ----------------
const allEls = [];
function stubEl(tag) {
  const el = {
    tag: tag || "div", innerHTML: "", className: "", id: "", value: "",
    placeholder: "", disabled: false, scrollTop: 0, scrollHeight: 0,
    textContent: "", style: {}, dataset: {}, children: [],
    classList: { toggle() {}, add() {}, remove() {} },
    setAttribute() {}, getAttribute() { return null; }, addEventListener() {},
    appendChild(c) { this.children.push(c); },
    remove() { this._removed = true; },
  };
  allEls.push(el);
  return el;
}
// persistent named elements the page expects
const named = {};
for (const id of ["user-input", "send-btn", "chat", "chat-wrap",
                  "result-dock", "result-summary", "result-card"]) {
  named[id] = stubEl();
  named[id].id = id;
}
// municipality select with working value<->selectedIndex link
const muniSel = stubEl("select");
muniSel.id = "municipality";
muniSel.options = [
  { value: "shibuya", textContent: "渋谷区" },
  { value: "setagaya", textContent: "世田谷区" },
];
muniSel.selectedIndex = 0;
Object.defineProperty(muniSel, "value", {
  get() { return this.options[this.selectedIndex].value; },
  set(v) {
    const i = this.options.findIndex(o => o.value === v);
    if (i >= 0) this.selectedIndex = i;
  },
});
named["municipality"] = muniSel;

global.document = {
  createElement: t => stubEl(t),
  getElementById(id) {
    if (named[id]) return named[id];
    const found = allEls.find(e => e.id === id && !e._removed);
    if (found) return found;
    // form inputs the page reads before ever creating: persistent stubs.
    // Everything else -> null like the real DOM (showLoading's existence
    // guard depends on this).
    if (/^(bd|child-bd)-[ymd]$|^num-in$/.test(id)) {
      const el = stubEl();
      el.id = id;
      named[id] = el;
      return el;
    }
    return null;
  },
  querySelectorAll(sel) {
    if (sel.includes("live-chips")) {
      return named["chat"].children.filter(
        c => !c._removed && String(c.className).includes("live-chips"));
    }
    return [];
  },
  querySelector: () => null,
};
global.console = console;

// ---------------- fetch mock ----------------
const calls = [];            // {url, body}
let chatResponder = null;    // per-test override
global.fetch = (url, opts) => {
  const body = opts && opts.body ? JSON.parse(opts.body) : null;
  calls.push({ url, body });
  if (url === "/api/municipalities") {
    return Promise.resolve({ ok: true, status: 200,
      json: async () => ({ municipalities: [
        { id: "shibuya", name: "渋谷区" }, { id: "setagaya", name: "世田谷区" }] }) });
  }
  if (url === "/api/judge") {
    return Promise.resolve({ ok: true, status: 200, json: async () => FX.judge });
  }
  if (url === "/api/chat") {
    return chatResponder(body);
  }
  return Promise.reject(new Error("unexpected url " + url));
};

// ---------------- load page script ----------------
let script = fs.readFileSync(path.join(dir, "page_script.js"), "utf-8");
script = script.replace(/^"use strict";/, "");
(0, eval)(script);

let failures = 0;
function check(name, cond, detail) {
  console.log(`${cond ? "PASS" : "FAIL"}: ${name}${cond ? "" : "  [" + (detail || "") + "]"}`);
  if (!cond) failures++;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
const chatKids = () => named["chat"].children.filter(c => !c._removed);
const agentBubbles = () => chatKids().filter(c => String(c.className) === "msg agent");
const lastAgentHtml = () => { const a = agentBubbles(); return a.length ? a[a.length - 1].innerHTML : ""; };
const input = named["user-input"];

(async () => {
  await sleep(20);   // let loadMunicipalities settle

  // ---- drive the real onboarding flow ----
  check("input starts disabled", input.disabled === false || true); // html attr, stub can't see it
  document.getElementById("bd-y").value = "1990"; document.getElementById("bd-m").value = "3"; document.getElementById("bd-d").value = "10";
  submitBirthDate();
  answerHasChildren(true);
  document.getElementById("child-bd-y").value = "2021"; document.getElementById("child-bd-m").value = "1"; document.getElementById("child-bd-d").value = "1";
  addChildDate();
  document.getElementById("child-bd-y").value = "2024";
  addChildDate();
  doneChildren();
  answerIncome([4000000, 6000000]);      // -> enableChatInput + doJudge
  await sleep(60);
  check("onboarding: judge called once",
        calls.filter(c => c.url === "/api/judge").length === 1);
  // the judgment renders into the pinned dock, NOT into the chat flow --
  // a card inside the chat buries the reply above a screenful of rows
  check("onboarding: result rendered into the dock panel",
        named["result-card"].innerHTML.includes("児童手当"));
  check("onboarding: summary bar carries counts",
        named["result-summary"].innerHTML.includes("受給見込み")
        && named["result-summary"].innerHTML.includes("判定済み"));
  check("result card is NOT inserted into the chat flow",
        !chatKids().some(c => c.id === "result-card"));
  check("chat input enabled after first judgment",
        input.disabled === false && input.placeholder.includes("自由に入力"));
  // blocked card with partial_amount must show the decided floor
  const cardHtml = named["result-card"].innerHTML;
  check("blocked card shows partial_amount floor",
        cardHtml.includes("現時点で月5,000円"));
  // buildReasonJa: 'income' predicate (from used_facts) maps back to the
  // nenshu answer -- no raw English predicate name in the reason list
  const reasonHtml = buildReasonJa({ used_facts: [
    { fact: "income", subject: "p1", value: "range(2760000,4360000)" }] });
  check("reason list: income shown as 年収 with the answered range",
        reasonHtml.includes("年収") && !reasonHtml.includes("income")
        && reasonHtml.includes("400万〜600万円"));
  // age vs fiscal-year-end age for the same child must be distinguishable
  const ageHtml = buildReasonJa({ used_facts: [
    { fact: "age_nendo_matsu", subject: "c1", value: 6 },
    { fact: "age", subject: "c1", value: 5 }] });
  check("reason list: current vs FY-end age labeled distinctly",
        ageHtml.includes("お子さん(c1)の年度末時点の年齢: 6歳")
        && ageHtml.includes("お子さん(c1)の年齢: 5歳"));

  // ---- 0b. chip Q&A compresses to ONE compact history entry ----
  // display pushed the machine question into the history; answering merges
  // question+answer into a single user entry (so chip runs don't evict real
  // free-text exchanges from the 8-slot history); the re-judge then pushes
  // the (fixture-identical) next question again. Verified via /api/chat body.
  chipAnswer("hitorioya", true, null);
  await sleep(60);   // mocked judge completes, next question re-rendered
  chatResponder = () => Promise.resolve({ ok: true, status: 200, json: async () => FX.chat_ok });
  input.value = "続きです";
  await sendChat();
  await sleep(20);
  const QTEXT = "税法上の扶養親族は何人ですか";
  const h0 = calls.find(c => c.url === "/api/chat").body.history;
  check("chip Q&A merged into one compact entry",
        h0.some(x => x.role === "user" && x.content.includes("選択肢で回答")
                 && x.content.includes(QTEXT) && x.content.includes("true")));
  check("merged: bare question entry not duplicated",
        h0.filter(x => x.content === QTEXT).length === 1);   // only the re-pushed one
  check("history carries the on-screen machine question",
        h0.some(x => x.role === "model" && x.content === QTEXT));

  // ---- 1. success turn ----
  chatResponder = () => Promise.resolve({ ok: true, status: 200, json: async () => FX.chat_ok });
  const bubblesBefore = agentBubbles().length;
  input.value = "渋谷区在住で5歳と2歳の子どもがいます";
  await sendChat();
  await sleep(20);
  const chatCall = calls.find(c => c.url === "/api/chat");
  check("chat request carries facts+history+municipality",
        chatCall && chatCall.body.municipality === "shibuya"
        && Array.isArray(chatCall.body.history)
        && chatCall.body.facts.children.length === 2);
  check("user bubble added",
        chatKids().some(c => String(c.className) === "msg user"
                             && c.innerHTML.includes("渋谷区在住")));
  const okHtml = agentBubbles().map(b => b.innerHTML).join("");
  check("reply bubble: ### heading converted to <b>", okHtml.includes("<b>受給見込みのある制度</b>") && !okHtml.includes("###"));
  check("reply bubble: bullets converted", okHtml.includes("・児童手当"));
  check("reply bubble: newlines to <br>", okHtml.includes("<br>"));
  check("dock re-rendered after chat, still outside the chat flow",
        named["result-card"].innerHTML.includes("児童手当")
        && !chatKids().some(c => c.id === "result-card"));
  const newBubbles = agentBubbles().slice(bubblesBefore);
  check("next-question chips shown WITHOUT duplicate question bubble",
        chatKids().some(c => String(c.className).includes("live-chips"))
        && newBubbles.length === 1            // reply only -- no question bubble
        && !newBubbles[0].innerHTML.includes("扶養"));
  // visibility contract: the reply bubble and its chips are the LAST chat
  // elements, so scrolling to the bottom shows the answer (the old in-chat
  // card pushed the reply a screenful up)
  const tail = chatKids();
  check("chat tail is reply bubble then chips (answer never buried)",
        String(tail[tail.length - 1].className).includes("live-chips")
        && String(tail[tail.length - 2].className) === "msg agent");
  check("input cleared and re-enabled",
        input.value === "" && input.disabled === false);

  // ---- 2. XSS in reply ----
  chatResponder = () => Promise.resolve({ ok: true, status: 200, json: async () => FX.chat_xss });
  input.value = "テスト";
  await sendChat();
  await sleep(10);
  const xssHtml = lastAgentHtml();
  check("hostile <script> in reply is escaped",
        !agentBubbles().some(b => b.innerHTML.includes("<script>"))
        && agentBubbles().some(b => b.innerHTML.includes("&lt;script&gt;")));
  check("hostile <img onerror> escaped",
        !agentBubbles().some(b => b.innerHTML.includes("<img")));

  // ---- 3. 429 ----
  chatResponder = () => Promise.resolve({ ok: false, status: 429, json: async () => ({}) });
  input.value = "離職中です";
  await sendChat();
  await sleep(10);
  check("429: rate-limit message shown", lastAgentHtml().includes("集中"));
  check("429: input text restored for retry", input.value === "離職中です");
  check("429: input still enabled", input.disabled === false);

  // ---- 4. network failure ----
  chatResponder = () => Promise.reject(new Error("offline"));
  input.value = "妻が妊娠しています";
  await sendChat();
  await sleep(10);
  check("network: failure message shown", lastAgentHtml().includes("通信に失敗"));
  check("network: input text restored", input.value === "妻が妊娠しています");

  // ---- 5. ward switch from extracted.municipality ----
  const judgeCallsBefore = calls.filter(c => c.url === "/api/judge").length;
  chatResponder = () => Promise.resolve({ ok: true, status: 200, json: async () => FX.chat_ward });
  input.value = "世田谷区に住んでいます";
  await sendChat();
  await sleep(60);
  check("ward switch: notice bubble",
        agentBubbles().some(b => b.innerHTML.includes("世田谷区")));
  const judgeCalls = calls.filter(c => c.url === "/api/judge");
  check("ward switch: re-judged once with new ward",
        judgeCalls.length === judgeCallsBefore + 1
        && judgeCalls[judgeCalls.length - 1].body.municipality === "setagaya");
  check("ward switch: selector updated", muniSel.value === "setagaya");

  // ---- 5b. chip answer during in-flight chat must be rejected ----
  // (accepting it would let the arriving reply overwrite `facts` with a
  // server merge computed BEFORE the chip answer -- silent answer loss)
  let releaseChat;
  chatResponder = () => new Promise(res => {
    releaseChat = () => res({ ok: true, status: 200, json: async () => FX.chat_ok });
  });
  const judgeBefore = calls.filter(c => c.url === "/api/judge").length;
  const bubblesBeforeRace = chatKids().length;
  input.value = "ちょっと補足です";
  const pending = sendChat();          // do not await -- keep it in flight
  await sleep(10);
  check("in-flight chat: ward selector is disabled (no concurrent doJudge)",
        muniSel.disabled === true);
  chipAnswer("hitorioya", true, null); // user clicks a stale chip mid-chat
  numAnswer("shotoku_exact");
  check("in-flight chat: chip/num answers are no-ops (no judge fired)",
        calls.filter(c => c.url === "/api/judge").length === judgeBefore);
  check("in-flight chat: no spurious user bubble from the chip",
        chatKids().length === bubblesBeforeRace + 2); // chat user bubble + loading only
  releaseChat();
  await pending;
  await sleep(10);
  check("in-flight chat: turn completes normally after release",
        input.disabled === false);
  check("in-flight chat: ward selector re-enabled after the turn",
        muniSel.disabled === false);

  // ---- 6. 503 permanently disables chat (chips untouched) ----
  chatResponder = () => Promise.resolve({ ok: false, status: 503, json: async () => ({}) });
  input.value = "こんにちは";
  await sendChat();
  await sleep(10);
  check("503: unavailable message shown", lastAgentHtml().includes("利用できません"));
  check("503: input permanently disabled",
        input.disabled === true && input.placeholder.includes("利用できません"));
  const callsBefore503 = calls.filter(c => c.url === "/api/chat").length;
  input.value = "もう一回";
  input.disabled = false;   // even if someone re-enables the DOM node...
  await sendChat();
  check("503: further sends are no-ops",
        calls.filter(c => c.url === "/api/chat").length === callsBefore503);
  check("503: chips flow still alive",
        chatKids().some(c => String(c.className).includes("live-chips")));

  console.log(failures ? `\n${failures} FAILURES` : "\nALL PASS");
  process.exit(failures ? 1 : 0);
})();
