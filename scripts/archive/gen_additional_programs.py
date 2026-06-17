#!/usr/bin/env python3
"""Generate additional programs batch 4: tax deductions, elderly, disability services.
Idempotent. Usage: python scripts/gen_additional_programs.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

RULES = {
    "shogaisha_koujo": """\
:- module(shogaisha_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(tokubetsu_shogaisha))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_1 ; G = shintai_2 ; G = seishin_1), !.
kettei_status(P, self, decided(kubun(ippan_shogaisha))) :-
    claimant(P), val(shogai_techo(P), _), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "hitorioya_koujo": """\
:- module(hitorioya_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), unknown(hitorioya(P)).

kettei_status(P, self, ineligible(not_hitorioya)) :-
    claimant(P), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(hitorioya_koujo))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kounenrei_koyou_keizoku": """\
:- module(kounenrei_koyou_keizoku, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \\+ age(P, _), !.
kettei_status(P, self, ineligible(under_60)) :-
    claimant(P), age(P, A), A < 60, !.
kettei_status(P, self, ineligible(over_65)) :-
    claimant(P), age(P, A), A >= 65, !.
kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kounenrei_keizoku))) :-
    claimant(P), age(P, A), A >= 60, A < 65, val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "jiritsu_shien_iryo_kousei": """\
:- module(jiritsu_shien_iryo_kousei, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kousei_iryo))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi, !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "hosougubi_shikyuu": """\
:- module(hosougubi_shikyuu, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(hosougubi))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi, !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "nichijou_seikatsu_yougu": """\
:- module(nichijou_seikatsu_yougu, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(yougu_kyufu))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi, !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "maisouryou": """\
:- module(maisouryou, [kettei_status/3, required_fact/3]).

required_fact(P, kenkou_hoken, "health insurance") :-
    claimant(P), unknown(kenkou_hoken(P)).

kettei_status(P, self, ineligible(no_kenkou_hoken)) :-
    claimant(P), val(kenkou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(amount(50000))) :-
    claimant(P), val(kenkou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "sousaihi": """\
:- module(sousaihi, [kettei_status/3, required_fact/3]).

required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), unknown(hoken_shubetsu(P)).

kettei_status(P, self, ineligible(not_kokuho)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \\= kokuho, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(amount(70000))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kinrou_gakusei_koujo": """\
:- module(kinrou_gakusei_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, daigaku_zaigaku, "university enrollment") :-
    claimant(P), unknown(daigaku_zaigaku(P)).

kettei_status(P, self, ineligible(not_enrolled)) :-
    claimant(P), val(daigaku_zaigaku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kinrou_gakusei))) :-
    claimant(P), val(daigaku_zaigaku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "shogaisha_koujo", "name": "障害者控除（所得税・住民税）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 270000,
     "statute": [{"ref": "所得税法79条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 障害者控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1160.htm"}],
     "cases": [
         {"name": "tokubetsu", "expect": {"subject": "self", "status": "decided", "detail": "kubun(tokubetsu_shogaisha)"},
          "facts": {"askable": {"shogai_techo": "shintai_1"}}},
         {"name": "ippan", "expect": {"subject": "self", "status": "decided", "detail": "kubun(ippan_shogaisha)"},
          "facts": {"askable": {"shogai_techo": "shintai_3"}}},
         {"name": "nashi", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
          "facts": {"askable": {"shogai_techo": "nashi"}}},
     ]},
    {"id": "hitorioya_koujo", "name": "ひとり親控除（所得税・住民税）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 350000,
     "statute": [{"ref": "所得税法81条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 ひとり親控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1171.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(hitorioya_koujo)"},
          "facts": {"askable": {"hitorioya": True}}},
         {"name": "not_hitorioya", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hitorioya"},
          "facts": {"askable": {"hitorioya": False}}},
     ]},
    {"id": "kounenrei_koyou_keizoku", "name": "高年齢雇用継続給付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 100000,
     "statute": [{"ref": "雇用保険法61条", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "ハローワーク 高年齢雇用継続給付", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_continue.html"}],
     "cases": [
         {"name": "eligible_62", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kounenrei_keizoku)"},
          "facts": {"claimant": {"birth_date": "1964-01-01"}, "askable": {"koyou_hoken": True}}},
         {"name": "under_60", "expect": {"subject": "self", "status": "ineligible", "detail": "under_60"},
          "facts": {"claimant": {"birth_date": "1990-01-01"}, "askable": {"koyou_hoken": True}}},
         {"name": "over_65", "expect": {"subject": "self", "status": "ineligible", "detail": "over_65"},
          "facts": {"claimant": {"birth_date": "1955-01-01"}, "askable": {"koyou_hoken": True}}},
     ]},
    {"id": "jiritsu_shien_iryo_kousei", "name": "自立支援医療（更生医療）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "障害者総合支援法52条", "url": "https://laws.e-gov.go.jp/law/417AC0000000123"},
                 {"ref": "厚労省 自立支援医療", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kousei_iryo)"},
          "facts": {"askable": {"shogai_techo": "shintai_1"}}},
         {"name": "nashi", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
          "facts": {"askable": {"shogai_techo": "nashi"}}},
     ]},
    {"id": "hosougubi_shikyuu", "name": "補装具費支給制度",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "障害者総合支援法76条", "url": "https://laws.e-gov.go.jp/law/417AC0000000123"},
                 {"ref": "厚労省 補装具費支給制度", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000078973.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(hosougubi)"},
          "facts": {"askable": {"shogai_techo": "shintai_2"}}},
         {"name": "nashi", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
          "facts": {"askable": {"shogai_techo": "nashi"}}},
     ]},
    {"id": "nichijou_seikatsu_yougu", "name": "日常生活用具給付等事業",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "障害者総合支援法77条", "url": "https://laws.e-gov.go.jp/law/417AC0000000123"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(yougu_kyufu)"},
          "facts": {"askable": {"shogai_techo": "ryoiku"}}},
         {"name": "nashi", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
          "facts": {"askable": {"shogai_techo": "nashi"}}},
     ]},
    {"id": "maisouryou", "name": "埋葬料・埋葬費（健康保険）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 50000,
     "statute": [{"ref": "健康保険法100条", "url": "https://laws.e-gov.go.jp/law/211AC0000000070"},
                 {"ref": "協会けんぽ 埋葬料", "url": "https://www.kyoukaikenpo.or.jp/g6/cat620/r307/"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "amount(50000)"},
          "facts": {"askable": {"kenkou_hoken": True}}},
         {"name": "no_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_kenkou_hoken"},
          "facts": {"askable": {"kenkou_hoken": False}}},
     ]},
    {"id": "sousaihi", "name": "葬祭費（国民健康保険）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "oneoff", "potential_amount": 70000,
     "statute": [{"ref": "国民健康保険法58条", "url": "https://hourei.net/law/333AC0000000192"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "amount(70000)"},
          "facts": {"askable": {"hoken_shubetsu": "kokuho"}}},
         {"name": "not_kokuho", "expect": {"subject": "self", "status": "ineligible", "detail": "not_kokuho"},
          "facts": {"askable": {"hoken_shubetsu": "shakai_hoken"}}},
     ]},
    {"id": "kinrou_gakusei_koujo", "name": "勤労学生控除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 270000,
     "statute": [{"ref": "所得税法82条", "url": "https://laws.e-gov.go.jp/law/340AC0000000033/"},
                 {"ref": "国税庁 勤労学生控除", "url": "https://www.nta.go.jp/taxes/shiraberu/taxanswer/shotoku/1175.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kinrou_gakusei)"},
          "facts": {"askable": {"daigaku_zaigaku": True}}},
         {"name": "not_enrolled", "expect": {"subject": "self", "status": "ineligible", "detail": "not_enrolled"},
          "facts": {"askable": {"daigaku_zaigaku": False}}},
     ]},
]

def main():
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
