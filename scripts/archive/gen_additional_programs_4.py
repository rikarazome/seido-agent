#!/usr/bin/env python3
"""Generate batch 7: final gap-fill from web research.
Idempotent. Usage: python scripts/gen_additional_programs_4.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

NEW_QUESTIONS = [
    {"fact": "haiguusha_shibou", "text": "配偶者を亡くされましたか", "type": "boolean", "sensitive": True},
    {"fact": "jutaku_shinchiku", "text": "今年、住宅の新築・購入・リフォームをしましたか（または予定ですか）", "type": "boolean"},
]

NEW_ASKABLE_MAP = {
    "haiguusha_shibou": ("haiguusha_shibou", "claimant"),
    "jutaku_shinchiku": ("jutaku_shinchiku", "claimant"),
}

RULES = {
    "izoku_kiso_nenkin": """\
:- module(izoku_kiso_nenkin, [kettei_status/3, required_fact/3]).

required_fact(P, haiguusha_shibou, "spouse death") :-
    claimant(P), unknown(haiguusha_shibou(P)).

kettei_status(P, self, ineligible(no_spouse_death)) :-
    claimant(P), val(haiguusha_shibou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(izoku_kiso))) :-
    claimant(P), val(haiguusha_shibou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "izoku_kousei_nenkin": """\
:- module(izoku_kousei_nenkin, [kettei_status/3, required_fact/3]).

required_fact(P, haiguusha_shibou, "spouse death") :-
    claimant(P), unknown(haiguusha_shibou(P)).

kettei_status(P, self, ineligible(no_spouse_death)) :-
    claimant(P), val(haiguusha_shibou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(izoku_kousei))) :-
    claimant(P), val(haiguusha_shibou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "mirai_eco_jutaku": """\
:- module(mirai_eco_jutaku, [kettei_status/3, required_fact/3]).

required_fact(P, jutaku_shinchiku, "housing construction") :-
    claimant(P), unknown(jutaku_shinchiku(P)).

kettei_status(P, self, ineligible(no_construction)) :-
    claimant(P), val(jutaku_shinchiku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(mirai_eco))) :-
    claimant(P), val(jutaku_shinchiku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "tokutei_shishutsu_koujo": """\
:- module(tokutei_shishutsu_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(not_salaryman)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(tokutei_shishutsu))) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "nisa_hikazei": """\
:- module(nisa_hikazei, [kettei_status/3]).
:- discontiguous required_fact/3.

kettei_status(P, self, decided(kubun(nisa_info))) :-
    claimant(P), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "seikatsu_fukushi_shikin": """\
:- module(seikatsu_fukushi_shikin, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, self, ineligible(not_low_income)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kinkyuu_koguchi))) :-
    claimant(P), val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "boshi_fukushi_shikin": """\
:- module(boshi_fukushi_shikin, [kettei_status/3, required_fact/3]).

required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), unknown(hitorioya(P)).

kettei_status(P, self, ineligible(not_hitorioya)) :-
    claimant(P), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(boshi_kashitsuke))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "izoku_kiso_nenkin", "name": "遺族基礎年金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 68000,
     "statute": [{"ref": "国民年金法37条", "url": "https://laws.e-gov.go.jp/law/334AC0000000141"},
                 {"ref": "日本年金機構 遺族基礎年金", "url": "https://www.nenkin.go.jp/service/jukyu/seido/izokunenkin/jukyu-yoken/20150401-04.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(izoku_kiso)"},
          "facts": {"askable": {"haiguusha_shibou": True}}},
         {"name": "no_death", "expect": {"subject": "self", "status": "ineligible", "detail": "no_spouse_death"},
          "facts": {"askable": {"haiguusha_shibou": False}}},
     ]},
    {"id": "izoku_kousei_nenkin", "name": "遺族厚生年金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 100000,
     "statute": [{"ref": "厚生年金保険法58条", "url": "https://laws.e-gov.go.jp/law/329AC0000000115/"},
                 {"ref": "日本年金機構 遺族厚生年金", "url": "https://www.nenkin.go.jp/service/jukyu/seido/izokunenkin/jukyu-yoken/20150424.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(izoku_kousei)"},
          "facts": {"askable": {"haiguusha_shibou": True}}},
         {"name": "no_death", "expect": {"subject": "self", "status": "ineligible", "detail": "no_spouse_death"},
          "facts": {"askable": {"haiguusha_shibou": False}}},
     ]},
    {"id": "mirai_eco_jutaku", "name": "みらいエコ住宅2026事業（住宅省エネ補助金）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 1250000,
     "statute": [{"ref": "国土交通省 みらいエコ住宅2026事業", "url": "https://www.mlit.go.jp/jutakukentiku/house/jutakukentiku_house_tk4_000243.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(mirai_eco)"},
          "facts": {"askable": {"jutaku_shinchiku": True}}},
         {"name": "no_construction", "expect": {"subject": "self", "status": "ineligible", "detail": "no_construction"},
          "facts": {"askable": {"jutaku_shinchiku": False}}},
     ]},
    {"id": "tokutei_shishutsu_koujo", "name": "特定支出控除（給与所得者の経費控除）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 500000,
     "statute": [{"ref": "所得税法57条の2", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 特定支出控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1415.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(tokutei_shishutsu)"},
          "facts": {"askable": {"koyou_hoken": True}}},
         {"name": "not_salaryman", "expect": {"subject": "self", "status": "ineligible", "detail": "not_salaryman"},
          "facts": {"askable": {"koyou_hoken": False}}},
     ]},
    {"id": "nisa_hikazei", "name": "NISA（少額投資非課税制度）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 0,
     "statute": [{"ref": "租税特別措置法37条の14", "url": "https://laws.e-gov.go.jp/law/332AC0000000026/"},
                 {"ref": "金融庁 NISA特設サイト", "url": "https://www.fsa.go.jp/policy/nisa2/index.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(nisa_info)"},
          "facts": {"askable": {}}},
     ]},
    {"id": "seikatsu_fukushi_shikin", "name": "生活福祉資金貸付制度（緊急小口資金等）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 100000,
     "statute": [{"ref": "生活福祉資金貸付制度要綱", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/seikatsuhogo/seikatsu-fukushi-shikin1/index.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kinkyuu_koguchi)"},
          "facts": {"askable": {"hikazei": True}}},
         {"name": "not_low_income", "expect": {"subject": "self", "status": "ineligible", "detail": "not_low_income"},
          "facts": {"askable": {"hikazei": False}}},
     ]},
    {"id": "boshi_fukushi_shikin", "name": "母子父子寡婦福祉資金貸付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 3000000,
     "statute": [{"ref": "母子及び父子並びに寡婦福祉法13条", "url": "https://laws.e-gov.go.jp/law/339AC0000000129/"},
                 {"ref": "厚労省 母子父子寡婦福祉資金貸付金", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000062986.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(boshi_kashitsuke)"},
          "facts": {"askable": {"hitorioya": True}}},
         {"name": "not_hitorioya", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hitorioya"},
          "facts": {"askable": {"hitorioya": False}}},
     ]},
]

def main():
    # 1. Add questions
    qs_path = REPO / "data" / "questions.yaml"
    qs = yaml.safe_load(qs_path.read_text(encoding="utf-8"))
    existing_facts = {q["fact"] for q in qs}
    insert_before = next(i for i, q in enumerate(qs) if q.get("scope") == "per_child")
    added = 0
    for nq in NEW_QUESTIONS:
        if nq["fact"] not in existing_facts:
            qs.insert(insert_before, nq)
            insert_before += 1
            added += 1
    qs_path.write_text(yaml.dump(qs, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"  questions.yaml: +{added}")

    # 2. Update factgen
    fg_path = REPO / "src" / "seido" / "factgen.py"
    fg = fg_path.read_text(encoding="utf-8")
    for key, (pred, scope) in NEW_ASKABLE_MAP.items():
        line = f'    "{key}": ("{pred}", "{scope}"),'
        if key not in fg:
            fg = fg.replace(
                '    "daigaku_zaigaku": ("daigaku_zaigaku", "claimant"),',
                f'    "daigaku_zaigaku": ("daigaku_zaigaku", "claimant"),\n{line}',
            )
    fg_path.write_text(fg, encoding="utf-8")
    print("  factgen.py: updated")

    # 3. Programs
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
