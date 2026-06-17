#!/usr/bin/env python3
"""Generate batch 5: programs requiring new askable keys.
Idempotent. Usage: python scripts/gen_additional_programs_2.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

NEW_QUESTIONS = [
    {"fact": "jiei_gyou", "text": "自営業・フリーランスですか（個人事業主ですか）", "type": "boolean"},
    {"fact": "taisyoku_kin", "text": "今年、退職金を受け取りましたか（または受け取る予定ですか）", "type": "boolean"},
    {"fact": "saigai_higai", "text": "昨年、災害・盗難・横領による損害がありましたか", "type": "boolean", "sensitive": True},
    {"fact": "juutaku_kaishu", "text": "住宅のバリアフリー改修・省エネ改修・耐震改修を行いましたか", "type": "boolean"},
]

NEW_ASKABLE_MAP = {
    "jiei_gyou": ("jiei_gyou", "claimant"),
    "taisyoku_kin": ("taisyoku_kin", "claimant"),
    "saigai_higai": ("saigai_higai", "claimant"),
    "juutaku_kaishu": ("juutaku_kaishu", "claimant"),
}

RULES = {
    "shoukibo_kigyou_kyousai": """\
:- module(shoukibo_kigyou_kyousai, [kettei_status/3, required_fact/3]).

required_fact(P, jiei_gyou, "self-employed status") :-
    claimant(P), unknown(jiei_gyou(P)).

kettei_status(P, self, ineligible(not_self_employed)) :-
    claimant(P), val(jiei_gyou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(shoukibo_kyousai))) :-
    claimant(P), val(jiei_gyou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "aoiro_shinkoku": """\
:- module(aoiro_shinkoku, [kettei_status/3, required_fact/3]).

required_fact(P, jiei_gyou, "self-employed status") :-
    claimant(P), unknown(jiei_gyou(P)).

kettei_status(P, self, ineligible(not_self_employed)) :-
    claimant(P), val(jiei_gyou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(aoiro_65man))) :-
    claimant(P), val(jiei_gyou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "taisyoku_shotoku_koujo": """\
:- module(taisyoku_shotoku_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, taisyoku_kin, "retirement benefit received") :-
    claimant(P), unknown(taisyoku_kin(P)).

kettei_status(P, self, ineligible(no_taisyoku_kin)) :-
    claimant(P), val(taisyoku_kin(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(taisyoku_koujo))) :-
    claimant(P), val(taisyoku_kin(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "zatsuzon_koujo": """\
:- module(zatsuzon_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, saigai_higai, "disaster/theft damage") :-
    claimant(P), unknown(saigai_higai(P)).

kettei_status(P, self, ineligible(no_damage)) :-
    claimant(P), val(saigai_higai(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(zatsuzon_koujo))) :-
    claimant(P), val(saigai_higai(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "juutaku_reform_zeisei": """\
:- module(juutaku_reform_zeisei, [kettei_status/3, required_fact/3]).

required_fact(P, juutaku_kaishu, "housing renovation") :-
    claimant(P), unknown(juutaku_kaishu(P)).

kettei_status(P, self, ineligible(no_renovation)) :-
    claimant(P), val(juutaku_kaishu(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(reform_zeisei))) :-
    claimant(P), val(juutaku_kaishu(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "saigai_gensai": """\
:- module(saigai_gensai, [kettei_status/3, required_fact/3]).

required_fact(P, saigai_higai, "disaster/theft damage") :-
    claimant(P), unknown(saigai_higai(P)).

kettei_status(P, self, ineligible(no_damage)) :-
    claimant(P), val(saigai_higai(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(saigai_gensai))) :-
    claimant(P), val(saigai_higai(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "shoukibo_kigyou_kyousai", "name": "小規模企業共済等掛金控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 840000,
     "statute": [{"ref": "所得税法75条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 小規模企業共済等掛金控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1135.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(shoukibo_kyousai)"},
          "facts": {"askable": {"jiei_gyou": True}}},
         {"name": "not_self_employed", "expect": {"subject": "self", "status": "ineligible", "detail": "not_self_employed"},
          "facts": {"askable": {"jiei_gyou": False}}},
     ]},
    {"id": "aoiro_shinkoku", "name": "青色申告特別控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 650000,
     "statute": [{"ref": "租税特別措置法25条の2", "url": "https://laws.e-gov.go.jp/law/332AC0000000026/"},
                 {"ref": "国税庁 青色申告特別控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/2072.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(aoiro_65man)"},
          "facts": {"askable": {"jiei_gyou": True}}},
         {"name": "not_self_employed", "expect": {"subject": "self", "status": "ineligible", "detail": "not_self_employed"},
          "facts": {"askable": {"jiei_gyou": False}}},
     ]},
    {"id": "taisyoku_shotoku_koujo", "name": "退職所得控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 8000000,
     "statute": [{"ref": "所得税法30条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 退職金と税", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1420.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(taisyoku_koujo)"},
          "facts": {"askable": {"taisyoku_kin": True}}},
         {"name": "no_retirement", "expect": {"subject": "self", "status": "ineligible", "detail": "no_taisyoku_kin"},
          "facts": {"askable": {"taisyoku_kin": False}}},
     ]},
    {"id": "zatsuzon_koujo", "name": "雑損控除（災害・盗難・横領）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 500000,
     "statute": [{"ref": "所得税法72条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 雑損控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1110.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(zatsuzon_koujo)"},
          "facts": {"askable": {"saigai_higai": True}}},
         {"name": "no_damage", "expect": {"subject": "self", "status": "ineligible", "detail": "no_damage"},
          "facts": {"askable": {"saigai_higai": False}}},
     ]},
    {"id": "juutaku_reform_zeisei", "name": "住宅リフォーム減税（バリアフリー・省エネ・耐震）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 250000,
     "statute": [{"ref": "租税特別措置法41条の3の2", "url": "https://laws.e-gov.go.jp/law/332AC0000000026/"},
                 {"ref": "国税庁 住宅リフォーム減税", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1219.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(reform_zeisei)"},
          "facts": {"askable": {"juutaku_kaishu": True}}},
         {"name": "no_renovation", "expect": {"subject": "self", "status": "ineligible", "detail": "no_renovation"},
          "facts": {"askable": {"juutaku_kaishu": False}}},
     ]},
    {"id": "saigai_gensai", "name": "災害減免法による所得税の軽減免除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 500000,
     "statute": [{"ref": "災害被害者に対する租税の減免、徴収猶予等に関する法律", "url": "https://laws.e-gov.go.jp/law/322AC0000000175/"},
                 {"ref": "国税庁 災害減免法", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1902.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(saigai_gensai)"},
          "facts": {"askable": {"saigai_higai": True}}},
         {"name": "no_damage", "expect": {"subject": "self", "status": "ineligible", "detail": "no_damage"},
          "facts": {"askable": {"saigai_higai": False}}},
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
