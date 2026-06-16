#!/usr/bin/env python3
"""Generate national programs for general adults (non-child, non-disability).

Idempotent: re-run overwrites existing files without duplication.
Usage: python scripts/gen_adult_programs.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

PROGRAMS = [
    {
        "id": "hikazei_setai_kyufukin",
        "name": "住民税非課税世帯向け給付金",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "oneoff",
        "potential_amount": 30000,
        "statute": [
            {"ref": "物価高騰対応重点支援地方創生臨時交付金（内閣府）", "url": "https://www.cao.go.jp/bunken-suishin/taisakukoufukin/taisakukoufukin_index.html"},
        ],
        "conditions": "hikazei=true, not seikatsu_hogo",
        "amount_val": 30000,
        "rule": """\
:- module(hikazei_setai_kyufukin, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(hikazei_setai_kyufukin, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(hikazei_setai_kyufukin, S, ineligible(receiving_seikatsu_hogo)) :-
    claimant(S), val(seikatsu_hogo(S), true), !.

kettei_status(hikazei_setai_kyufukin, S, ineligible(not_hikazei)) :-
    claimant(S), val(hikazei(S), false), !.

required_fact(P, hikazei, "住民税非課税かどうか") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, seikatsu_hogo, "生活保護の受給") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(hikazei_setai_kyufukin, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(hikazei_setai_kyufukin, S, decided(amount(30000))) :-
    claimant(S), val(hikazei(S), true), no(seikatsu_hogo(S)), !.

kettei_status(hikazei_setai_kyufukin, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "hikazei_eligible", "facts": {"askable": {"hikazei": True, "seikatsu_hogo": False}}, "expect": {"status": "decided", "amount": 30000}},
            {"name": "not_hikazei", "facts": {"askable": {"hikazei": False}}, "expect": {"status": "ineligible"}},
            {"name": "seikatsu_hogo", "facts": {"askable": {"hikazei": True, "seikatsu_hogo": True}}, "expect": {"status": "ineligible"}},
            {"name": "unknown_hikazei", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "shitsugyo_kyufu",
        "name": "雇用保険基本手当（失業給付）",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "monthly",
        "potential_amount": 200000,
        "statute": [
            {"ref": "雇用保険法10条〜35条", "url": "https://hourei.net/law/349AC0000000116"},
            {"ref": "ハローワーク 雇用保険の基本手当", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_basicbenefit.html"},
        ],
        "conditions": "koyou_hoken=true, rishoku=true",
        "amount_val": None,
        "rule": """\
:- module(shitsugyo_kyufu, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(shitsugyo_kyufu, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(shitsugyo_kyufu, S, ineligible(not_enrolled_koyou_hoken)) :-
    claimant(S), val(koyou_hoken(S), false), !.

kettei_status(shitsugyo_kyufu, S, ineligible(not_rishoku)) :-
    claimant(S), val(rishoku(S), false), !.

required_fact(P, koyou_hoken, "雇用保険の加入") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, rishoku, "離職中かどうか") :-
    claimant(P), unknown(rishoku(P)).

kettei_status(shitsugyo_kyufu, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(shitsugyo_kyufu, S, decided(kubun(kihon_teate))) :-
    claimant(S), val(koyou_hoken(S), true), val(rishoku(S), true), !.

kettei_status(shitsugyo_kyufu, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "eligible", "facts": {"askable": {"koyou_hoken": True, "rishoku": True}}, "expect": {"status": "decided"}},
            {"name": "not_enrolled", "facts": {"askable": {"koyou_hoken": False, "rishoku": True}}, "expect": {"status": "ineligible"}},
            {"name": "not_rishoku", "facts": {"askable": {"koyou_hoken": True, "rishoku": False}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "kyushokusha_shien_kunren",
        "name": "求職者支援制度（職業訓練受講給付金）",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "monthly",
        "potential_amount": 100000,
        "statute": [
            {"ref": "職業訓練の実施等による特定求職者の就職の支援に関する法律7条", "url": "https://hourei.net/law/423AC0000000047"},
            {"ref": "厚労省 求職者支援制度", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/koyou/kyushokusha_shien/index.html"},
        ],
        "conditions": "rishoku=true, koyou_hoken=false (or not receiving unemployment)",
        "amount_val": 100000,
        "rule": """\
:- module(kyushokusha_shien_kunren, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(kyushokusha_shien_kunren, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(kyushokusha_shien_kunren, S, ineligible(not_rishoku)) :-
    claimant(S), val(rishoku(S), false), !.

kettei_status(kyushokusha_shien_kunren, S, ineligible(has_koyou_hoken)) :-
    claimant(S), val(koyou_hoken(S), true), !.

required_fact(P, rishoku, "離職中かどうか") :-
    claimant(P), unknown(rishoku(P)).
required_fact(P, koyou_hoken, "雇用保険の加入") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(kyushokusha_shien_kunren, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(kyushokusha_shien_kunren, S, decided(amount(100000))) :-
    claimant(S), val(rishoku(S), true), val(koyou_hoken(S), false), !.

kettei_status(kyushokusha_shien_kunren, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "eligible", "facts": {"askable": {"rishoku": True, "koyou_hoken": False}}, "expect": {"status": "decided", "amount": 100000}},
            {"name": "has_koyou_hoken", "facts": {"askable": {"rishoku": True, "koyou_hoken": True}}, "expect": {"status": "ineligible"}},
            {"name": "not_rishoku", "facts": {"askable": {"rishoku": False, "koyou_hoken": False}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "jukyo_kakuho_kyufukin",
        "name": "住居確保給付金",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "monthly",
        "potential_amount": 53700,
        "statute": [
            {"ref": "生活困窮者自立支援法4条・5条", "url": "https://hourei.net/law/425AC0000000105"},
            {"ref": "厚労省 住居確保給付金", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000073432.html"},
        ],
        "conditions": "rishoku=true, income limit",
        "amount_val": None,
        "rule": """\
:- module(jukyo_kakuho_kyufukin, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(jukyo_kakuho_kyufukin, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(jukyo_kakuho_kyufukin, S, ineligible(receiving_seikatsu_hogo)) :-
    claimant(S), val(seikatsu_hogo(S), true), !.

kettei_status(jukyo_kakuho_kyufukin, S, ineligible(not_rishoku)) :-
    claimant(S), val(rishoku(S), false), !.

required_fact(P, rishoku, "離職中かどうか") :-
    claimant(P), unknown(rishoku(P)).
required_fact(P, seikatsu_hogo, "生活保護の受給") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(jukyo_kakuho_kyufukin, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(jukyo_kakuho_kyufukin, S, decided(kubun(jukyo_kakuho))) :-
    claimant(S), val(rishoku(S), true), no(seikatsu_hogo(S)), !.

kettei_status(jukyo_kakuho_kyufukin, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "eligible", "facts": {"askable": {"rishoku": True, "seikatsu_hogo": False}}, "expect": {"status": "decided"}},
            {"name": "not_rishoku", "facts": {"askable": {"rishoku": False}}, "expect": {"status": "ineligible"}},
            {"name": "seikatsu_hogo", "facts": {"askable": {"rishoku": True, "seikatsu_hogo": True}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "kokuho_keigen",
        "name": "国民健康保険料の軽減（7割・5割・2割）",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "yearly",
        "potential_amount": 200000,
        "statute": [
            {"ref": "国民健康保険法81条、国民健康保険法施行令29条の7", "url": "https://hourei.net/law/333AC0000000192"},
            {"ref": "厚労省 国民健康保険の保険料軽減", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/iryouhoken/iryouhoken01/index.html"},
        ],
        "conditions": "hoken_shubetsu=kokuho, income limit",
        "amount_val": None,
        "rule": """\
:- module(kokuho_keigen, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(kokuho_keigen, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(kokuho_keigen, S, ineligible(not_kokuho)) :-
    claimant(S), val(hoken_shubetsu(S), T), T \\= kokuho, !.

kettei_status(kokuho_keigen, S, ineligible(income_exceeds_limit)) :-
    claimant(S), val(hoken_shubetsu(S), kokuho),
    income_known(S, I), I > 3_000_000, !.

required_fact(P, hoken_shubetsu, "健康保険の種類") :-
    claimant(P), unknown(hoken_shubetsu(P)).
required_fact(P, income, "年収") :-
    claimant(P), val(hoken_shubetsu(P), kokuho), unknown(income(P)).

kettei_status(kokuho_keigen, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(kokuho_keigen, S, decided(kubun(keigen_7wari))) :-
    claimant(S), val(hoken_shubetsu(S), kokuho),
    income_known(S, I), I =< 430_000, !.

kettei_status(kokuho_keigen, S, decided(kubun(keigen_5wari))) :-
    claimant(S), val(hoken_shubetsu(S), kokuho),
    income_known(S, I), I =< 1_050_000, !.

kettei_status(kokuho_keigen, S, decided(kubun(keigen_2wari))) :-
    claimant(S), val(hoken_shubetsu(S), kokuho),
    income_known(S, I), I =< 3_000_000, !.

kettei_status(kokuho_keigen, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "keigen_7wari", "facts": {"askable": {"hoken_shubetsu": "kokuho", "nenshu": 1000000}}, "expect": {"status": "decided"}},
            {"name": "keigen_5wari", "facts": {"askable": {"hoken_shubetsu": "kokuho", "nenshu": 2000000}}, "expect": {"status": "decided"}},
            {"name": "keigen_2wari", "facts": {"askable": {"hoken_shubetsu": "kokuho", "nenshu": 4000000}}, "expect": {"status": "decided"}},
            {"name": "not_kokuho", "facts": {"askable": {"hoken_shubetsu": "shakai_hoken"}}, "expect": {"status": "ineligible"}},
            {"name": "income_too_high", "facts": {"askable": {"hoken_shubetsu": "kokuho", "nenshu": 8000000}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "kokumin_nenkin_menjo",
        "name": "国民年金保険料の免除・猶予",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "monthly",
        "potential_amount": 16980,
        "statute": [
            {"ref": "国民年金法90条・90条の2", "url": "https://hourei.net/law/334AC0000000141"},
            {"ref": "日本年金機構 国民年金保険料の免除制度", "url": "https://www.nenkin.go.jp/service/kokunen/menjo/20150428.html"},
        ],
        "conditions": "income limit (shotoku-based)",
        "amount_val": 16980,
        "rule": """\
:- module(kokumin_nenkin_menjo, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(kokumin_nenkin_menjo, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(kokumin_nenkin_menjo, S, ineligible(receiving_seikatsu_hogo)) :-
    claimant(S), val(seikatsu_hogo(S), true), !.

kettei_status(kokumin_nenkin_menjo, S, ineligible(income_exceeds_limit)) :-
    claimant(S), income_known(S, I), I > 3_600_000, !.

required_fact(P, income, "年収") :-
    claimant(P), unknown(income(P)).
required_fact(P, seikatsu_hogo, "生活保護の受給") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(kokumin_nenkin_menjo, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(kokumin_nenkin_menjo, S, decided(kubun(zenmen))) :-
    claimant(S), income_known(S, I), I =< 670_000, no(seikatsu_hogo(S)), !.

kettei_status(kokumin_nenkin_menjo, S, decided(kubun(menjo_3_4))) :-
    claimant(S), income_known(S, I), I =< 1_180_000, no(seikatsu_hogo(S)), !.

kettei_status(kokumin_nenkin_menjo, S, decided(kubun(menjo_half))) :-
    claimant(S), income_known(S, I), I =< 1_680_000, no(seikatsu_hogo(S)), !.

kettei_status(kokumin_nenkin_menjo, S, decided(kubun(menjo_1_4))) :-
    claimant(S), income_known(S, I), I =< 2_280_000, no(seikatsu_hogo(S)), !.

kettei_status(kokumin_nenkin_menjo, S, decided(kubun(yuuyo))) :-
    claimant(S), income_known(S, I), I =< 3_600_000, no(seikatsu_hogo(S)), !.

kettei_status(kokumin_nenkin_menjo, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "zenmen", "facts": {"askable": {"nenshu": 1000000, "seikatsu_hogo": False}}, "expect": {"status": "decided"}},
            {"name": "yuuyo", "facts": {"askable": {"nenshu": 5000000, "seikatsu_hogo": False}}, "expect": {"status": "decided"}},
            {"name": "income_too_high", "facts": {"askable": {"nenshu": 8000000, "seikatsu_hogo": False}}, "expect": {"status": "ineligible"}},
            {"name": "seikatsu_hogo", "facts": {"askable": {"nenshu": 1000000, "seikatsu_hogo": True}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "shoubyou_teatekin",
        "name": "傷病手当金",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "monthly",
        "potential_amount": 200000,
        "statute": [
            {"ref": "健康保険法99条", "url": "https://hourei.net/law/211AC0000000070"},
            {"ref": "全国健康保険協会 傷病手当金", "url": "https://www.kyoukaikenpo.or.jp/g3/sb3040/r139/"},
        ],
        "conditions": "hoken_shubetsu=shakai_hoken, byouki_kyugyou=true",
        "amount_val": None,
        "rule": """\
:- module(shoubyou_teatekin, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(shoubyou_teatekin, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(shoubyou_teatekin, S, ineligible(not_shakai_hoken)) :-
    claimant(S), val(hoken_shubetsu(S), T), T \\= shakai_hoken, !.

kettei_status(shoubyou_teatekin, S, ineligible(not_byouki_kyugyou)) :-
    claimant(S), val(byouki_kyugyou(S), false), !.

required_fact(P, hoken_shubetsu, "健康保険の種類") :-
    claimant(P), unknown(hoken_shubetsu(P)).
required_fact(P, byouki_kyugyou, "病気休業中かどうか") :-
    claimant(P), unknown(byouki_kyugyou(P)).

kettei_status(shoubyou_teatekin, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(shoubyou_teatekin, S, decided(kubun(shoubyou_teate))) :-
    claimant(S), val(hoken_shubetsu(S), shakai_hoken), val(byouki_kyugyou(S), true), !.

kettei_status(shoubyou_teatekin, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "eligible", "facts": {"askable": {"hoken_shubetsu": "shakai_hoken", "byouki_kyugyou": True}}, "expect": {"status": "decided"}},
            {"name": "not_shakai_hoken", "facts": {"askable": {"hoken_shubetsu": "kokuho", "byouki_kyugyou": True}}, "expect": {"status": "ineligible"}},
            {"name": "not_sick", "facts": {"askable": {"hoken_shubetsu": "shakai_hoken", "byouki_kyugyou": False}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
    {
        "id": "kyouiku_kunren_kyufu",
        "name": "教育訓練給付金",
        "layer": "national",
        "subject": "claimant",
        "unit": "per_household",
        "amount_type": "oneoff",
        "potential_amount": 100000,
        "statute": [
            {"ref": "雇用保険法60条の2", "url": "https://hourei.net/law/349AC0000000116"},
            {"ref": "ハローワーク 教育訓練給付制度", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_education.html"},
        ],
        "conditions": "koyou_hoken=true (or past enrollment)",
        "amount_val": None,
        "rule": """\
:- module(kyouiku_kunren_kyufu, [kettei_status/3, required_fact/3]).
:- use_module('../engine').

kettei_status(kyouiku_kunren_kyufu, S, error(structural)) :-
    \\+ claimant(S), !.

kettei_status(kyouiku_kunren_kyufu, S, ineligible(no_koyou_hoken)) :-
    claimant(S), val(koyou_hoken(S), false), !.

required_fact(P, koyou_hoken, "雇用保険の加入") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(kyouiku_kunren_kyufu, S, blocked(Missing)) :-
    claimant(S), findall(F, required_fact(S, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.

kettei_status(kyouiku_kunren_kyufu, S, decided(kubun(ippan_kyouiku))) :-
    claimant(S), val(koyou_hoken(S), true), !.

kettei_status(kyouiku_kunren_kyufu, _, error(no_rule_matched)).
""",
        "cases": [
            {"name": "eligible", "facts": {"askable": {"koyou_hoken": True}}, "expect": {"status": "decided"}},
            {"name": "no_koyou_hoken", "facts": {"askable": {"koyou_hoken": False}}, "expect": {"status": "ineligible"}},
            {"name": "unknown", "facts": {"askable": {}}, "expect": {"status": "blocked"}},
        ],
    },
]


def main():
    programs_path = REPO / "data" / "programs.yaml"
    existing = yaml.safe_load(programs_path.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in existing}

    for prog in PROGRAMS:
        pid = prog["id"]

        # --- Prolog rule ---
        rule_path = REPO / "rules" / "national" / f"{pid}.pl"
        rule_path.write_text(prog["rule"], encoding="utf-8")
        print(f"  rule: {rule_path.relative_to(REPO)}")

        # --- golden test directory ---
        golden_dir = REPO / "tests" / "golden" / pid
        golden_dir.mkdir(parents=True, exist_ok=True)

        # statute_source.md
        statute_md = f"# {prog['name']}\n\n"
        for s in prog["statute"]:
            statute_md += f"- {s['ref']}: {s['url']}\n"
        statute_md += f"\n## Conditions\n{prog['conditions']}\n"
        (golden_dir / "statute_source.md").write_text(statute_md, encoding="utf-8")

        # cases.yaml
        cases = []
        for c in prog["cases"]:
            case = {
                "name": c["name"],
                "as_of": "2026-06-15",
                "municipality": "shibuya",
                "facts": c["facts"],
            }
            if c["expect"]["status"] == "decided":
                if "amount" in c["expect"]:
                    case["expect"] = f"decided(amount({c['expect']['amount']}))"
                else:
                    case["expect_prefix"] = "decided("
            elif c["expect"]["status"] == "ineligible":
                case["expect_prefix"] = "ineligible("
            elif c["expect"]["status"] == "blocked":
                case["expect_prefix"] = "blocked("
            cases.append(case)

        (golden_dir / "cases.yaml").write_text(
            yaml.dump(cases, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8")
        print(f"  golden: {golden_dir.relative_to(REPO)}")

        # --- programs.yaml entry ---
        if pid not in existing_ids:
            entry = {
                "id": pid,
                "name": prog["name"],
                "layer": prog["layer"],
                "municipality": None,
                "subject": prog["subject"],
                "unit": prog["unit"],
                "amount_type": prog["amount_type"],
                "potential_amount": prog["potential_amount"],
                "status": "supported",
                "statute": prog["statute"],
            }
            existing.append(entry)
            existing_ids.add(pid)
            print(f"  programs.yaml: added {pid}")
        else:
            print(f"  programs.yaml: {pid} already exists")

    programs_path.write_text(
        yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8")
    print(f"\nDone: {len(PROGRAMS)} programs generated.")


if __name__ == "__main__":
    main()
