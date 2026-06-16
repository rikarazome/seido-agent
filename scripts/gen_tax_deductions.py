#!/usr/bin/env python3
"""Generate tax deduction / savings programs for general adults.
Idempotent. Usage: python scripts/gen_tax_deductions.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

# New askable keys needed: haiguusha (spouse), jutaku_loan (housing loan),
# iryouhi_10man (medical expenses > 10万), seimei_hoken (life insurance)
NEW_QUESTIONS = [
    {"fact": "haiguusha", "text": "配偶者（パートナー）はいますか", "type": "boolean"},
    {"fact": "jutaku_loan", "text": "住宅ローンを組んでいますか（または過去10年以内に組みましたか）", "type": "boolean"},
    {"fact": "iryouhi_10man", "text": "昨年の医療費の自己負担合計が10万円を超えていますか（家族合算）", "type": "boolean"},
    {"fact": "seimei_hoken", "text": "生命保険・医療保険に加入していますか", "type": "boolean"},
    {"fact": "jishin_hoken", "text": "地震保険に加入していますか", "type": "boolean"},
]

NEW_ASKABLE_MAP = {
    "haiguusha": ("haiguusha", "claimant"),
    "jutaku_loan": ("jutaku_loan", "claimant"),
    "iryouhi_10man": ("iryouhi_10man", "claimant"),
    "seimei_hoken": ("seimei_hoken", "claimant"),
    "jishin_hoken": ("jishin_hoken", "claimant"),
}

RULES = {
    "iryouhi_koujo": """\
:- module(iryouhi_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, iryouhi_10man, "medical expenses over 100k") :-
    claimant(P), unknown(iryouhi_10man(P)).

kettei_status(P, self, ineligible(under_10man)) :-
    claimant(P), val(iryouhi_10man(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(iryouhi_koujo))) :-
    claimant(P), val(iryouhi_10man(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "self_medication": """\
:- module(self_medication, [kettei_status/3, required_fact/3]).

required_fact(P, iryouhi_10man, "medical expenses check") :-
    claimant(P), unknown(iryouhi_10man(P)).

kettei_status(P, self, ineligible(iryouhi_koujo_available)) :-
    claimant(P), val(iryouhi_10man(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(self_medication))) :-
    claimant(P), val(iryouhi_10man(P), false), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "furusato_nouzei": """\
:- module(furusato_nouzei, [kettei_status/3, required_fact/3]).

required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(furusato_nouzei))) :-
    claimant(P), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "ideco_koujo": """\
:- module(ideco_koujo, [kettei_status/3, required_fact/3]).

kettei_status(P, self, decided(kubun(ideco_koujo))) :-
    claimant(P), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "seimei_hoken_koujo": """\
:- module(seimei_hoken_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, seimei_hoken, "life insurance enrollment") :-
    claimant(P), unknown(seimei_hoken(P)).

kettei_status(P, self, ineligible(no_seimei_hoken)) :-
    claimant(P), val(seimei_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(seimei_hoken_koujo))) :-
    claimant(P), val(seimei_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "jishin_hoken_koujo": """\
:- module(jishin_hoken_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, jishin_hoken, "earthquake insurance") :-
    claimant(P), unknown(jishin_hoken(P)).

kettei_status(P, self, ineligible(no_jishin_hoken)) :-
    claimant(P), val(jishin_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(jishin_hoken_koujo))) :-
    claimant(P), val(jishin_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "jutaku_loan_koujo": """\
:- module(jutaku_loan_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, jutaku_loan, "housing loan") :-
    claimant(P), unknown(jutaku_loan(P)).

kettei_status(P, self, ineligible(no_jutaku_loan)) :-
    claimant(P), val(jutaku_loan(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(jutaku_loan_koujo))) :-
    claimant(P), val(jutaku_loan(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "haiguusha_koujo": """\
:- module(haiguusha_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, haiguusha, "spouse status") :-
    claimant(P), unknown(haiguusha(P)).

kettei_status(P, self, ineligible(no_haiguusha)) :-
    claimant(P), val(haiguusha(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(haiguusha_koujo))) :-
    claimant(P), val(haiguusha(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "iryouhi_koujo", "name": "医療費控除（確定申告）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 50000,
     "statute": [{"ref": "所得税法73条", "url": "https://hourei.net/law/340AC0000000033"},
                 {"ref": "国税庁 医療費控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1120.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(iryouhi_koujo)"},
          "facts": {"askable": {"iryouhi_10man": True}}},
         {"name": "under_10man", "expect": {"subject": "self", "status": "ineligible", "detail": "under_10man"},
          "facts": {"askable": {"iryouhi_10man": False}}},
     ]},
    {"id": "self_medication", "name": "セルフメディケーション税制",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 20000,
     "statute": [{"ref": "租税特別措置法41条の17の2", "url": "https://hourei.net/law/332AC0000000026"},
                 {"ref": "国税庁 セルフメディケーション税制", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1129.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(self_medication)"},
          "facts": {"askable": {"iryouhi_10man": False}}},
         {"name": "iryouhi_koujo_priority", "expect": {"subject": "self", "status": "ineligible", "detail": "iryouhi_koujo_available"},
          "facts": {"askable": {"iryouhi_10man": True}}},
     ]},
    {"id": "furusato_nouzei", "name": "ふるさと納税（寄附金控除）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 100000,
     "statute": [{"ref": "地方税法37条の2", "url": "https://hourei.net/law/325AC0000000226"},
                 {"ref": "総務省 ふるさと納税", "url": "https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/mechanism/deduction.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(furusato_nouzei)"},
          "facts": {"askable": {"seikatsu_hogo": False}}},
         {"name": "seikatsu_hogo", "expect": {"subject": "self", "status": "ineligible", "detail": "seikatsu_hogo"},
          "facts": {"askable": {"seikatsu_hogo": True}}},
     ]},
    {"id": "ideco_koujo", "name": "iDeCo（個人型確定拠出年金）の所得控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 276000,
     "statute": [{"ref": "確定拠出年金法3条", "url": "https://hourei.net/law/413AC0000000088"},
                 {"ref": "iDeCo公式サイト", "url": "https://www.ideco-koushiki.jp/"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(ideco_koujo)"},
          "facts": {"askable": {}}},
     ]},
    {"id": "seimei_hoken_koujo", "name": "生命保険料控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 120000,
     "statute": [{"ref": "所得税法76条", "url": "https://hourei.net/law/340AC0000000033"},
                 {"ref": "国税庁 生命保険料控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1140.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(seimei_hoken_koujo)"},
          "facts": {"askable": {"seimei_hoken": True}}},
         {"name": "not_enrolled", "expect": {"subject": "self", "status": "ineligible", "detail": "no_seimei_hoken"},
          "facts": {"askable": {"seimei_hoken": False}}},
     ]},
    {"id": "jishin_hoken_koujo", "name": "地震保険料控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 50000,
     "statute": [{"ref": "所得税法77条", "url": "https://hourei.net/law/340AC0000000033"},
                 {"ref": "国税庁 地震保険料控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1145.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(jishin_hoken_koujo)"},
          "facts": {"askable": {"jishin_hoken": True}}},
         {"name": "not_enrolled", "expect": {"subject": "self", "status": "ineligible", "detail": "no_jishin_hoken"},
          "facts": {"askable": {"jishin_hoken": False}}},
     ]},
    {"id": "jutaku_loan_koujo", "name": "住宅ローン減税（住宅借入金等特別控除）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 400000,
     "statute": [{"ref": "租税特別措置法41条", "url": "https://hourei.net/law/332AC0000000026"},
                 {"ref": "国税庁 住宅ローン減税", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1211-1.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(jutaku_loan_koujo)"},
          "facts": {"askable": {"jutaku_loan": True}}},
         {"name": "no_loan", "expect": {"subject": "self", "status": "ineligible", "detail": "no_jutaku_loan"},
          "facts": {"askable": {"jutaku_loan": False}}},
     ]},
    {"id": "haiguusha_koujo", "name": "配偶者控除・配偶者特別控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 380000,
     "statute": [{"ref": "所得税法83条・83条の2", "url": "https://hourei.net/law/340AC0000000033"},
                 {"ref": "国税庁 配偶者控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1191.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(haiguusha_koujo)"},
          "facts": {"askable": {"haiguusha": True}}},
         {"name": "no_spouse", "expect": {"subject": "self", "status": "ineligible", "detail": "no_haiguusha"},
          "facts": {"askable": {"haiguusha": False}}},
     ]},
]


def main():
    # 1. Add questions
    qs_path = REPO / "data" / "questions.yaml"
    qs = yaml.safe_load(qs_path.read_text(encoding="utf-8"))
    existing_facts = {q["fact"] for q in qs}
    insert_before = next(i for i, q in enumerate(qs) if q.get("scope") == "per_child")
    added_qs = 0
    for nq in NEW_QUESTIONS:
        if nq["fact"] not in existing_facts:
            qs.insert(insert_before, nq)
            insert_before += 1
            added_qs += 1
    qs_path.write_text(yaml.dump(qs, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"  questions.yaml: +{added_qs} questions")

    # 2. Update factgen.py ASKABLE_MAP
    fg_path = REPO / "src" / "seido" / "factgen.py"
    fg = fg_path.read_text(encoding="utf-8")
    for key, (pred, scope) in NEW_ASKABLE_MAP.items():
        line = f'    "{key}": ("{pred}", "{scope}"),'
        if key not in fg:
            fg = fg.replace(
                '    "byouki_kyugyou": ("byouki_kyugyou", "claimant"),',
                f'    "byouki_kyugyou": ("byouki_kyugyou", "claimant"),\n{line}',
            )
    fg_path.write_text(fg, encoding="utf-8")
    print("  factgen.py: updated ASKABLE_MAP")

    # 3. Write rules, golden tests, programs.yaml
    programs_path = REPO / "data" / "programs.yaml"
    existing = yaml.safe_load(programs_path.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in existing}

    for prog in PROGRAMS:
        pid = prog["id"]
        rule_text = RULES[pid]
        rp = REPO / "rules" / "national" / f"{pid}.pl"
        rp.write_text(rule_text, encoding="utf-8")

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
            existing_ids.add(pid)
            print(f"  + {pid}")

    programs_path.write_text(yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"\nDone. {len(PROGRAMS)} programs.")


if __name__ == "__main__":
    main()
