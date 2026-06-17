#!/usr/bin/env python3
"""Generate batch 3: pregnancy, caregiving, education, elderly programs.
Idempotent. Usage: python scripts/gen_adult_programs_3.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

RULES = {
    "ninpu_kensin_josei": """\
:- module(ninpu_kensin_josei, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), val(ninshin(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kensin_14kai))) :-
    claimant(P), val(ninshin(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "sanzen_sango_nenkin_menjo": """\
:- module(sanzen_sango_nenkin_menjo, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), val(ninshin(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(menjo_4months))) :-
    claimant(P), val(ninshin(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "shussan_teatekin": """\
:- module(shussan_teatekin, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).
required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), val(ninshin(P), true), unknown(hoken_shubetsu(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), val(ninshin(P), false), !.
kettei_status(P, self, ineligible(not_shakai_hoken)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \\= shakai_hoken, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(shussan_teate))) :-
    claimant(P), val(ninshin(P), true), val(hoken_shubetsu(P), shakai_hoken), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "ikuji_kyuugyou_kyufu": """\
:- module(ikuji_kyuugyou_kyufu, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(ikuji_kyuugyou))) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kaigo_kyuugyou_kyufu": """\
:- module(kaigo_kyuugyou_kyufu, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, kaigo_family, "family caregiving status") :-
    claimant(P), unknown(kaigo_family(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_kaigo)) :-
    claimant(P), val(kaigo_family(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kaigo_kyuugyou))) :-
    claimant(P), val(koyou_hoken(P), true), val(kaigo_family(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "koutou_kyouiku_shien": """\
:- module(koutou_kyouiku_shien, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, daigaku_zaigaku, "university enrollment") :-
    claimant(P), unknown(daigaku_zaigaku(P)).

kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, ineligible(not_enrolled)) :-
    claimant(P), val(daigaku_zaigaku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(jugyo_menjo))) :-
    claimant(P), val(hikazei(P), true), val(daigaku_zaigaku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kyufu_shougakukin": """\
:- module(kyufu_shougakukin, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, daigaku_zaigaku, "university enrollment") :-
    claimant(P), unknown(daigaku_zaigaku(P)).

kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, ineligible(not_enrolled)) :-
    claimant(P), val(daigaku_zaigaku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(amount(75800))) :-
    claimant(P), val(hikazei(P), true), val(daigaku_zaigaku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "silver_pass": """\
:- module(silver_pass, [kettei_status/3, required_fact/3]).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \\+ age(P, _), !.
kettei_status(P, self, ineligible(under_70)) :-
    claimant(P), age(P, A), A < 70, !.
kettei_status(P, self, decided(kubun(silver_pass))) :-
    claimant(P), age(P, A), A >= 70, !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kaigo_hokenryo_genmen": """\
:- module(kaigo_hokenryo_genmen, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), age(P, A), A >= 65, unknown(hikazei(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \\+ age(P, _), !.
kettei_status(P, self, ineligible(under_65)) :-
    claimant(P), age(P, A), A < 65, !.
kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), age(P, A), A >= 65, val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), age(P, A), A >= 65,
    findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(genmen))) :-
    claimant(P), age(P, A), A >= 65, val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kougaku_kaigo_service": """\
:- module(kougaku_kaigo_service, [kettei_status/3, required_fact/3]).

required_fact(P, kaigo_nintei, "kaigo nintei level") :-
    claimant(P), unknown(kaigo_nintei(P)).

kettei_status(P, self, ineligible(no_kaigo_nintei)) :-
    claimant(P), val(kaigo_nintei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kougaku_kaigo))) :-
    claimant(P), val(kaigo_nintei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {"id": "ninpu_kensin_josei", "name": "妊婦健康診査の公費助成（14回分）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "母子保健法13条", "url": "https://hourei.net/law/340AC0000000141"},
                 {"ref": "厚労省 妊婦健診の公費負担", "url": "https://www.mhlw.go.jp/bunya/kodomo/boshi-hoken13/"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kensin_14kai)"},
          "facts": {"askable": {"ninshin": True}}},
         {"name": "not_pregnant", "expect": {"subject": "self", "status": "ineligible", "detail": "not_pregnant"},
          "facts": {"askable": {"ninshin": False}}},
     ]},
    {"id": "sanzen_sango_nenkin_menjo", "name": "産前産後の国民年金保険料免除",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 16980,
     "statute": [{"ref": "国民年金法88条の2", "url": "https://hourei.net/law/334AC0000000141"},
                 {"ref": "日本年金機構 産前産後の免除制度", "url": "https://www.nenkin.go.jp/service/kokunen/menjo/20180810.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(menjo_4months)"},
          "facts": {"askable": {"ninshin": True}}},
         {"name": "not_pregnant", "expect": {"subject": "self", "status": "ineligible", "detail": "not_pregnant"},
          "facts": {"askable": {"ninshin": False}}},
     ]},
    {"id": "shussan_teatekin", "name": "出産手当金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 200000,
     "statute": [{"ref": "健康保険法102条", "url": "https://hourei.net/law/211AC0000000070"},
                 {"ref": "全国健康保険協会 出産手当金", "url": "https://www.kyoukaikenpo.or.jp/g6/cat620/r311/"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(shussan_teate)"},
          "facts": {"askable": {"ninshin": True, "hoken_shubetsu": "shakai_hoken"}}},
         {"name": "not_pregnant", "expect": {"subject": "self", "status": "ineligible", "detail": "not_pregnant"},
          "facts": {"askable": {"ninshin": False}}},
         {"name": "kokuho", "expect": {"subject": "self", "status": "ineligible", "detail": "not_shakai_hoken"},
          "facts": {"askable": {"ninshin": True, "hoken_shubetsu": "kokuho"}}},
     ]},
    {"id": "ikuji_kyuugyou_kyufu", "name": "育児休業給付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 300000,
     "statute": [{"ref": "雇用保険法61条の7", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "ハローワーク 育児休業給付金", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_continue.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(ikuji_kyuugyou)"},
          "facts": {"askable": {"koyou_hoken": True}}},
         {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
          "facts": {"askable": {"koyou_hoken": False}}},
     ]},
    {"id": "kaigo_kyuugyou_kyufu", "name": "介護休業給付金",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 200000,
     "statute": [{"ref": "雇用保険法61条の4", "url": "https://hourei.net/law/349AC0000000116"},
                 {"ref": "ハローワーク 介護休業給付金", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_continue.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kaigo_kyuugyou)"},
          "facts": {"askable": {"koyou_hoken": True, "kaigo_family": True}}},
         {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
          "facts": {"askable": {"koyou_hoken": False}}},
         {"name": "not_kaigo", "expect": {"subject": "self", "status": "ineligible", "detail": "not_kaigo"},
          "facts": {"askable": {"koyou_hoken": True, "kaigo_family": False}}},
     ]},
    {"id": "koutou_kyouiku_shien", "name": "高等教育の修学支援新制度（大学等無償化）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "大学等における修学の支援に関する法律", "url": "https://hourei.net/law/501AC0000000008"},
                 {"ref": "文科省 高等教育の修学支援新制度", "url": "https://www.mext.go.jp/a_menu/koutou/hutankeigen/index.htm"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(jugyo_menjo)"},
          "facts": {"askable": {"hikazei": True, "daigaku_zaigaku": True}}},
         {"name": "not_hikazei", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hikazei"},
          "facts": {"askable": {"hikazei": False}}},
         {"name": "not_enrolled", "expect": {"subject": "self", "status": "ineligible", "detail": "not_enrolled"},
          "facts": {"askable": {"hikazei": True, "daigaku_zaigaku": False}}},
     ]},
    {"id": "kyufu_shougakukin", "name": "給付型奨学金（JASSO）",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "monthly", "potential_amount": 75800,
     "statute": [{"ref": "独立行政法人日本学生支援機構法", "url": "https://hourei.net/law/415AC0000000094"},
                 {"ref": "JASSO 給付奨学金", "url": "https://www.jasso.go.jp/shogakukin/moshikomi/yoyaku/index.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "amount(75800)"},
          "facts": {"askable": {"hikazei": True, "daigaku_zaigaku": True}}},
         {"name": "not_hikazei", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hikazei"},
          "facts": {"askable": {"hikazei": False}}},
     ]},
    {"id": "silver_pass", "name": "東京都シルバーパス",
     "layer": "municipal", "municipality": "tokyo",
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "東京都シルバーパス条例", "url": "https://www.fukushi.metro.tokyo.lg.jp/kourei/shisaku/silverpass.html"}],
     "cases": [
         {"name": "eligible_70", "expect": {"subject": "self", "status": "decided", "detail": "kubun(silver_pass)"},
          "facts": {"claimant": {"birth_date": "1950-01-01"}, "askable": {}}},
         {"name": "under_70", "expect": {"subject": "self", "status": "ineligible", "detail": "under_70"},
          "facts": {"claimant": {"birth_date": "1990-01-01"}, "askable": {}}},
     ]},
    {"id": "kaigo_hokenryo_genmen", "name": "介護保険料の減免",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "yearly", "potential_amount": 50000,
     "statute": [{"ref": "介護保険法142条", "url": "https://hourei.net/law/409AC0000000123"},
                 {"ref": "厚労省 介護保険料の減免", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/kaigo_koureisha/gaiyo/index.html"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(genmen)"},
          "facts": {"claimant": {"birth_date": "1950-01-01"}, "askable": {"hikazei": True}}},
         {"name": "under_65", "expect": {"subject": "self", "status": "ineligible", "detail": "under_65"},
          "facts": {"claimant": {"birth_date": "1990-01-01"}, "askable": {"hikazei": True}}},
         {"name": "not_hikazei", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hikazei"},
          "facts": {"claimant": {"birth_date": "1950-01-01"}, "askable": {"hikazei": False}}},
     ]},
    {"id": "kougaku_kaigo_service", "name": "高額介護サービス費",
     "layer": "national", "municipality": None,
     "subject": "claimant", "unit": "per_household", "amount_type": "in_kind", "potential_amount": 0,
     "statute": [{"ref": "介護保険法51条", "url": "https://hourei.net/law/409AC0000000123"}],
     "cases": [
         {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kougaku_kaigo)"},
          "facts": {"askable": {"kaigo_nintei": True}}},
         {"name": "no_kaigo", "expect": {"subject": "self", "status": "ineligible", "detail": "no_kaigo_nintei"},
          "facts": {"askable": {"kaigo_nintei": False}}},
     ]},
]

def main():
    programs_path = REPO / "data" / "programs.yaml"
    existing = yaml.safe_load(programs_path.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in existing}
    for prog in PROGRAMS:
        pid = prog["id"]
        rule_text = RULES[pid]
        if prog["layer"] == "national":
            rp = REPO / "rules" / "national" / f"{pid}.pl"
        else:
            rp = REPO / "rules" / "municipal" / prog["municipality"] / f"{pid}.pl"
        rp.parent.mkdir(parents=True, exist_ok=True)
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
        else:
            print(f"  = {pid}")
    programs_path.write_text(yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False), encoding="utf-8")
    print(f"\nDone. {len(PROGRAMS)} programs.")

if __name__ == "__main__":
    main()
