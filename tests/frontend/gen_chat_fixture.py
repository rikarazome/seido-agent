# -*- coding: utf-8 -*-
"""Build chat-harness fixtures from a REAL judge_request run (no Gemini).

Produces chat_fixtures.json with:
  judge     -- real /api/judge-shaped response (onboarding doJudge mock)
  chat_ok   -- /api/chat-shaped success turn (real judgment + canned reply)
  chat_xss  -- reply containing hostile markup (escaping check)
  chat_ward -- extracted.municipality=setagaya (ward-switch path)
"""
import io
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "src"))
from seido.runner import judge_request

FACTS = {"children": [{"id": "c1", "birth_date": "2021-01-01", "askable": {}},
                      {"id": "c2", "birth_date": "2024-01-01", "askable": {}}],
         "askable": {"nenshu": [4000000, 6000000]}}
AS_OF = date(2026, 7, 8)

judge = judge_request(FACTS, AS_OF, "shibuya")

# contract-shaped synthetic: give one blocked card a partial_amount so the
# harness can pin the 「現時点で月◯円」 rendering (real ones need a
# mixed decided/blocked household, rare in this fixture's facts)
for _r in judge["results"]:
    if _r["status"] == "blocked":
        _r["partial_amount"] = {"type": "monthly", "yen": 5000}
        break

REPLY = ("お子さん2人の情報を確認しました。\n"
         "**受給見込みのある制度**\n"
         "* 児童手当（月額25,000円）\n"
         "* 018サポート（月額10,000円）\n"
         "正確な判断は自治体窓口でご確認ください。")

def chat_resp(reply, ward=None):
    return {
        "response": reply,
        "facts": FACTS,
        "extracted": {"claimant_birth_date": None,
                      "children": None,
                      "municipality": ward,
                      "askable": {}, "confidence": "high",
                      "clarification_needed": None},
        "judgment": {"headline": judge["headline"],
                     "results": judge["results"]},
        "next_question": judge["next_question"],
    }

fixtures = {
    "judge": judge,
    "chat_ok": chat_resp(REPLY),
    "chat_xss": chat_resp('お調べしました <script>alert(1)</script> <img src=x onerror=alert(2)>'),
    "chat_ward": chat_resp("世田谷区で判定し直しますね。", ward="setagaya"),
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "chat_fixtures.json")
io.open(out, "w", encoding="utf-8").write(json.dumps(fixtures, ensure_ascii=False))
nq = judge["next_question"]
print("fixture written; next_question fact =", nq and nq["fact"],
      "| results =", len(judge["results"]))
