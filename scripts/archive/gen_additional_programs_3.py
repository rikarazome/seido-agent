#!/usr/bin/env python3
"""Generate batch 6: missing programs found by web research.
Idempotent. Usage: python scripts/gen_additional_programs_3.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

RULES = {
    "nenkin_seikatsusha_shien": """\
:- module(nenkin_seikatsusha_shien, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \\+ age(P, _), !.
kettei_status(P, self, ineligible(under_65)) :-
    claimant(P), age(P, A), A < 65, !.
kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(amount(5620))) :-
    claimant(P), age(P, A), A >= 65, val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kourei_sai_shushoku": """\
:- module(kourei_sai_shushoku, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, rishoku, "rishoku status") :-
    claimant(P), unknown(rishoku(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \\+ age(P, _), !.
kettei_status(P, self, ineligible(under_60)) :-
    claimant(P), age(P, A), A < 60, !.
kettei_status(P, self, ineligible(over_65)) :-
    claimant(P), age(P, A), A >= 65, !.
kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_rishoku)) :-
    claimant(P), val(rishoku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kourei_sai_shushoku))) :-
    claimant(P), age(P, A), A >= 60, A < 65,
    val(koyou_hoken(P), true), val(rishoku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "tokutei_kyouiku_kunren": """\
:- module(tokutei_kyouiku_kunren, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(tokutei_kyouiku))) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "senmon_jissen_kyouiku": """\
:- module(senmon_jissen_kyouiku, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(senmon_jissen))) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "bukka_kodomo_teate": """\
:- module(bukka_kodomo_teate, [kettei_status/3, required_fact/3]).
:- discontiguous required_fact/3.

kettei_status(_, C, ineligible(no_child)) :-
    \\+ child(C), !.
kettei_status(_, C, decided(amount(20000))) :-
    child(C), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "seikatsu_hogo_seido": """\
:- module(seikatsu_hogo_seido, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(not_eligible)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, decided(kubun(seikatsu_hogo_annai))) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(seikatsu_hogo_soudan))) :-
    claimant(P), val(hikazei(P), true), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "nenkin_seikatsusha_shien", "name": "年金生活者支援給付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 5620,
     "statute": [{"ref": "年金生活者支援給付金の支給に関する法律", "url": "https://laws.e-gov.go.jp/law/424AC0000000102/"},
                 {"ref": "日本年金機構 年金生活者支援給付金", "url": "https://www.nenkin.go.jp/service/jukyu/sonota-kyufu/shienkyufukin/20190401.html"}],
     "cases": [
         {"name": "eligible_70", "expect": {"subject": "self", "status": "decided", "detail": "amount(5620)"},
          "facts": {"claimant": {"birth_date": "1950-01-01"}, "askable": {"hikazei": True}}},
         {"name": "under_65", "expect": {"subject": "self", "status": "ineligible", "detail": "under_65"},
          "facts": {"claimant": {"birth_date": "1990-01-01"}, "askable": {"hikazei": True}}},
         {"name": "not_hikazei", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hikazei"},
          "facts": {"claimant": {"birth_date": "1950-01-01"}, "askable": {"hikazei": False}}},
     ]},
    {"id": "kourei_sai_shushoku", "name": "高年齢再就職給付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 100000,
     "statute": [{"ref": "雇用保険法61条の2", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "ハローワーク 高年齢再就職給付金", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_continue.html"}],
     "cases": [
         {"name": "eligible_62", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kourei_sai_shushoku)"},
          "facts": {"claimant": {"birth_date": "1964-01-01"}, "askable": {"koyou_hoken": True, "rishoku": True}}},
         {"name": "under_60", "expect": {"subject": "self", "status": "ineligible", "detail": "under_60"},
          "facts": {"claimant": {"birth_date": "1990-01-01"}, "askable": {"koyou_hoken": True, "rishoku": True}}},
     ]},
    {"id": "tokutei_kyouiku_kunren", "name": "特定一般教育訓練給付金（受講費40%）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 200000,
     "statute": [{"ref": "雇用保険法60条の2", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "厚労省 教育訓練給付制度", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/jinzaikaihatsu/kyouiku.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(tokutei_kyouiku)"},
          "facts": {"askable": {"koyou_hoken": True}}},
         {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
          "facts": {"askable": {"koyou_hoken": False}}},
     ]},
    {"id": "senmon_jissen_kyouiku", "name": "専門実践教育訓練給付金（受講費70%）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 560000,
     "statute": [{"ref": "雇用保険法60条の2", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "厚労省 専門実践教育訓練", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/jinzaikaihatsu/kyouiku.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(senmon_jissen)"},
          "facts": {"askable": {"koyou_hoken": True}}},
         {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
          "facts": {"askable": {"koyou_hoken": False}}},
     ]},
    {"id": "bukka_kodomo_teate", "name": "物価高対応子育て応援手当（子ども1人2万円）",
     "layer": "national", "municipality": None,
     "subject": "child", "unit": "per_child", "amount_type": "oneoff", "potential_amount": 20000,
     "statute": [{"ref": "こども家庭庁 物価高対応子育て応援手当", "url": "https://www.cfa.go.jp/policies/kokoseido/jidouteate/annai"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "c1", "status": "decided", "detail": "amount(20000)"},
          "facts": {"children": [{"id": "c1", "birth_date": "2020-01-01"}], "askable": {}}},
     ]},
    {"id": "seikatsu_hogo_seido", "name": "生活保護制度（相談案内）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 130000,
     "statute": [{"ref": "生活保護法", "url": "https://laws.e-gov.go.jp/law/325AC0000000144/"},
                 {"ref": "厚労省 生活保護制度", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/seikatsuhogo/seikatuhogo/index.html"}],
     "cases": [
         {"name": "already_receiving", "expect": {"subject": "self", "status": "decided", "detail": "kubun(seikatsu_hogo_annai)"},
          "facts": {"askable": {"seikatsu_hogo": True}}},
         {"name": "hikazei_soudan", "expect": {"subject": "self", "status": "decided", "detail": "kubun(seikatsu_hogo_soudan)"},
          "facts": {"askable": {"hikazei": True, "seikatsu_hogo": False}}},
         {"name": "not_eligible", "expect": {"subject": "self", "status": "ineligible", "detail": "not_eligible"},
          "facts": {"askable": {"hikazei": False}}},
     ]},
]

def main():
    programs_path = REPO / "data" / "programs.yaml"
    existing = yaml.safe_load(programs_path.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in existing}
    for prog in PROGRAMS:
        pid = prog["id"]
        rp = REPO / "rules" / "national" / f"{pid}.pl"
        rp.write_text(RULES[pid], encoding="utf-8")
        gd = REPO / "tests" / "golden" / pid
        gd.mkdir(parents=True, exist_ok=True)
        cases = [{"name": c["name"], "as_of": "2026-06-15", "municipality": "shibuya",
                  "facts": c["facts"], "expect": c["expect"]} for c in prog["cases"]]
        (gd / "cases.yaml").write_text(yaml.dump(cases, allow_unicode=True, sort_keys=False), encoding="utf-8")
        st = f"# {prog['name']}\n\n" + "".join(f"- {s['ref']}: {s['url']}\n" for s in prog["statute"])
        (gd / "statute_source.md").write_text(st, encoding="utf-8")
        if pid not in existing_ids:
            entry = {k: prog[k] for k in ["id","name","layer","municipality","subject","unit","amount_type","potential_amount"]}
            entry["status"] = "supported"
            entry["statute"] = prog["statute"]
            existing.append(entry)
            print(f"  + {pid}")
    programs_path.write_text(yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"\nDone. {len(PROGRAMS)} programs.")

if __name__ == "__main__":
    main()
