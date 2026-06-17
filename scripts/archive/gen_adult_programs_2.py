#!/usr/bin/env python3
"""Generate additional national/tokyo programs for general adults (batch 2).
Idempotent. Usage: python scripts/gen_adult_programs_2.py
"""
from pathlib import Path
import yaml

REPO = Path(__file__).resolve().parents[1]

RULES_TPL = {
    "sai_shushoku_teate": """\
:- module(sai_shushoku_teate, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, rishoku, "rishoku status") :-
    claimant(P), unknown(rishoku(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_rishoku)) :-
    claimant(P), val(rishoku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(sai_shushoku))) :-
    claimant(P), val(koyou_hoken(P), true), val(rishoku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "kougaku_ryouyouhi": """\
:- module(kougaku_ryouyouhi, [kettei_status/3, required_fact/3]).

required_fact(P, kenkou_hoken, "health insurance") :-
    claimant(P), unknown(kenkou_hoken(P)).

kettei_status(P, self, ineligible(no_kenkou_hoken)) :-
    claimant(P), val(kenkou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kougaku_ryouyou))) :-
    claimant(P), val(kenkou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "nyuuin_shokuji_gengaku": """\
:- module(nyuuin_shokuji_gengaku, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(gengaku))) :-
    claimant(P), val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "nhk_menjo": """\
:- module(nhk_menjo, [kettei_status/3, required_fact/3]).

required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).
required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), no(seikatsu_hogo(P)), unknown(shogai_techo(P)).
required_fact(P, hikazei, "hikazei status") :-
    claimant(P), no(seikatsu_hogo(P)), unknown(hikazei(P)).

kettei_status(P, self, decided(kubun(zenmen_seiho))) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, decided(kubun(zenmen_shougai))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi,
    val(hikazei(P), true), !.
kettei_status(P, self, ineligible(not_eligible)) :-
    claimant(P), no(seikatsu_hogo(P)),
    (val(shogai_techo(P), nashi) ; (val(shogai_techo(P), _), val(hikazei(P), false))), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "boshi_jiritsu_kyouiku": """\
:- module(boshi_jiritsu_kyouiku, [kettei_status/3, required_fact/3]).

required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), unknown(hitorioya(P)).

kettei_status(P, self, ineligible(not_hitorioya)) :-
    claimant(P), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(jiritsu_kyouiku))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "boshi_koutou_kunren": """\
:- module(boshi_koutou_kunren, [kettei_status/3, required_fact/3]).

required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), unknown(hitorioya(P)).

kettei_status(P, self, ineligible(not_hitorioya)) :-
    claimant(P), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(amount(100000))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "shougai_kiso_nenkin": """\
:- module(shougai_kiso_nenkin, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

taisho_toukyu(shintai_1).
taisho_toukyu(shintai_2).
taisho_toukyu(seishin_1).
taisho_toukyu(seishin_2).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, ineligible(grade_not_covered)) :-
    claimant(P), val(shogai_techo(P), G), \\+ taisho_toukyu(G), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(kiso_1kyu))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_1 ; G = seishin_1), !.
kettei_status(P, self, decided(kubun(kiso_2kyu))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_2 ; G = seishin_2), !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "toei_kotsu_muryou": """\
:- module(toei_kotsu_muryou, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(muryou_pass))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi, !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "tokyo_suidou_genmen": """\
:- module(tokyo_suidou_genmen, [kettei_status/3, required_fact/3]).

required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).
required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), no(seikatsu_hogo(P)), unknown(shogai_techo(P)).
required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), no(seikatsu_hogo(P)),
    (val(shogai_techo(P), nashi) ; unknown(shogai_techo(P))),
    unknown(hitorioya(P)).

kettei_status(P, self, decided(kubun(seiho_menjo))) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, decided(kubun(shougai_genmen))) :-
    claimant(P), val(shogai_techo(P), G), G \\= nashi, !.
kettei_status(P, self, decided(kubun(hitorioya_genmen))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(P, self, ineligible(not_eligible)) :-
    claimant(P), no(seikatsu_hogo(P)),
    val(shogai_techo(P), nashi), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(_, _, error(no_rule_matched)).
""",
    "sai_shushoku_teate_koyou": """\
:- module(sai_shushoku_teate_koyou, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \\= [], !.
kettei_status(P, self, decided(kubun(ippan))) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
""",
}

PROGRAMS = [
    {
        "id": "sai_shushoku_teate",
        "name": "再就職手当",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "oneoff", "potential_amount": 300000,
        "statute": [
            {"ref": "雇用保険法56条の3", "url": "https://hourei.net/law/349AC0000000116"},
            {"ref": "ハローワーク 再就職手当", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_stepup.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(sai_shushoku)"},
             "facts": {"askable": {"koyou_hoken": True, "rishoku": True}}},
            {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
             "facts": {"askable": {"koyou_hoken": False}}},
            {"name": "not_rishoku", "expect": {"subject": "self", "status": "ineligible", "detail": "not_rishoku"},
             "facts": {"askable": {"koyou_hoken": True, "rishoku": False}}},
        ],
    },
    {
        "id": "kougaku_ryouyouhi",
        "name": "高額療養費制度",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "in_kind", "potential_amount": 0,
        "statute": [
            {"ref": "健康保険法115条", "url": "https://hourei.net/law/211AC0000000070"},
            {"ref": "厚労省 高額療養費制度", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/iryouhoken/juuyou/kougakuiryou/index.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kougaku_ryouyou)"},
             "facts": {"askable": {"kenkou_hoken": True}}},
            {"name": "no_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_kenkou_hoken"},
             "facts": {"askable": {"kenkou_hoken": False}}},
        ],
    },
    {
        "id": "nyuuin_shokuji_gengaku",
        "name": "入院時食事療養費の標準負担額減額",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "in_kind", "potential_amount": 0,
        "statute": [
            {"ref": "健康保険法85条", "url": "https://hourei.net/law/211AC0000000070"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(gengaku)"},
             "facts": {"askable": {"hikazei": True}}},
            {"name": "not_hikazei", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hikazei"},
             "facts": {"askable": {"hikazei": False}}},
        ],
    },
    {
        "id": "nhk_menjo",
        "name": "NHK受信料の免除",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "monthly", "potential_amount": 2200,
        "statute": [
            {"ref": "放送法64条、日本放送協会放送受信料免除基準", "url": "https://www.nhk.or.jp/reception/exemption/"},
        ],
        "cases": [
            {"name": "seiho", "expect": {"subject": "self", "status": "decided", "detail": "kubun(zenmen_seiho)"},
             "facts": {"askable": {"seikatsu_hogo": True}}},
            {"name": "shougai_hikazei", "expect": {"subject": "self", "status": "decided", "detail": "kubun(zenmen_shougai)"},
             "facts": {"askable": {"seikatsu_hogo": False, "shogai_techo": "shintai_1", "hikazei": True}}},
            {"name": "not_eligible", "expect": {"subject": "self", "status": "ineligible", "detail": "not_eligible"},
             "facts": {"askable": {"seikatsu_hogo": False, "shogai_techo": "nashi"}}},
        ],
    },
    {
        "id": "boshi_jiritsu_kyouiku",
        "name": "ひとり親家庭自立支援教育訓練給付金",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "oneoff", "potential_amount": 200000,
        "statute": [
            {"ref": "母子及び父子並びに寡婦福祉法31条", "url": "https://hourei.net/law/339AC0000000129"},
            {"ref": "厚労省 母子家庭自立支援給付金", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000062986.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(jiritsu_kyouiku)"},
             "facts": {"askable": {"hitorioya": True}}},
            {"name": "not_hitorioya", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hitorioya"},
             "facts": {"askable": {"hitorioya": False}}},
        ],
    },
    {
        "id": "boshi_koutou_kunren",
        "name": "ひとり親家庭高等職業訓練促進給付金",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "monthly", "potential_amount": 100000,
        "statute": [
            {"ref": "母子及び父子並びに寡婦福祉法31条の2", "url": "https://hourei.net/law/339AC0000000129"},
            {"ref": "厚労省 高等職業訓練促進給付金", "url": "https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000062986.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "amount(100000)"},
             "facts": {"askable": {"hitorioya": True}}},
            {"name": "not_hitorioya", "expect": {"subject": "self", "status": "ineligible", "detail": "not_hitorioya"},
             "facts": {"askable": {"hitorioya": False}}},
        ],
    },
    {
        "id": "shougai_kiso_nenkin",
        "name": "障害基礎年金",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "monthly", "potential_amount": 83700,
        "statute": [
            {"ref": "国民年金法30条〜36条の4", "url": "https://hourei.net/law/334AC0000000141"},
            {"ref": "日本年金機構 障害基礎年金", "url": "https://www.nenkin.go.jp/service/jukyu/shougainenkin/jukyu-yoken/20150401-01.html"},
        ],
        "cases": [
            {"name": "kiso_1kyu", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kiso_1kyu)"},
             "facts": {"askable": {"shogai_techo": "shintai_1"}}},
            {"name": "kiso_2kyu", "expect": {"subject": "self", "status": "decided", "detail": "kubun(kiso_2kyu)"},
             "facts": {"askable": {"shogai_techo": "shintai_2"}}},
            {"name": "no_techo", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
             "facts": {"askable": {"shogai_techo": "nashi"}}},
            {"name": "grade_3", "expect": {"subject": "self", "status": "ineligible", "detail": "grade_not_covered"},
             "facts": {"askable": {"shogai_techo": "shintai_3"}}},
        ],
    },
    {
        "id": "toei_kotsu_muryou",
        "name": "都営交通無料乗車券",
        "layer": "municipal", "municipality": "tokyo",
        "subject": "claimant", "unit": "per_household",
        "amount_type": "in_kind", "potential_amount": 0,
        "statute": [
            {"ref": "東京都福祉保健局 都営交通無料乗車券", "url": "https://www.fukushi.metro.tokyo.lg.jp/shinsho/nichijo/muryou.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(muryou_pass)"},
             "facts": {"askable": {"shogai_techo": "shintai_1"}}},
            {"name": "no_techo", "expect": {"subject": "self", "status": "ineligible", "detail": "no_shogai_techo"},
             "facts": {"askable": {"shogai_techo": "nashi"}}},
        ],
    },
    {
        "id": "tokyo_suidou_genmen",
        "name": "水道料金の減免（東京都水道局）",
        "layer": "municipal", "municipality": "tokyo",
        "subject": "claimant", "unit": "per_household",
        "amount_type": "monthly", "potential_amount": 5000,
        "statute": [
            {"ref": "東京都水道局 水道料金・下水道料金の減免", "url": "https://www.waterworks.metro.tokyo.lg.jp/tetsuduki/ryokin/genmen.html"},
        ],
        "cases": [
            {"name": "seiho", "expect": {"subject": "self", "status": "decided", "detail": "kubun(seiho_menjo)"},
             "facts": {"askable": {"seikatsu_hogo": True}}},
            {"name": "shougai", "expect": {"subject": "self", "status": "decided", "detail": "kubun(shougai_genmen)"},
             "facts": {"askable": {"seikatsu_hogo": False, "shogai_techo": "shintai_1"}}},
            {"name": "hitorioya", "expect": {"subject": "self", "status": "decided", "detail": "kubun(hitorioya_genmen)"},
             "facts": {"askable": {"seikatsu_hogo": False, "shogai_techo": "nashi", "hitorioya": True}}},
            {"name": "not_eligible", "expect": {"subject": "self", "status": "ineligible", "detail": "not_eligible"},
             "facts": {"askable": {"seikatsu_hogo": False, "shogai_techo": "nashi", "hitorioya": False}}},
        ],
    },
    {
        "id": "shuugyou_sokushin_teate",
        "name": "就業促進定着手当",
        "layer": "national", "municipality": None,
        "subject": "claimant", "unit": "per_household",
        "amount_type": "oneoff", "potential_amount": 100000,
        "statute": [
            {"ref": "雇用保険法56条の3第3項", "url": "https://hourei.net/law/349AC0000000116"},
            {"ref": "ハローワーク 就業促進定着手当", "url": "https://www.hellowork.mhlw.go.jp/insurance/insurance_stepup.html"},
        ],
        "cases": [
            {"name": "eligible", "expect": {"subject": "self", "status": "decided", "detail": "kubun(ippan)"},
             "facts": {"askable": {"koyou_hoken": True}}},
            {"name": "no_koyou_hoken", "expect": {"subject": "self", "status": "ineligible", "detail": "no_koyou_hoken"},
             "facts": {"askable": {"koyou_hoken": False}}},
        ],
    },
]

def main():
    programs_path = REPO / "data" / "programs.yaml"
    existing = yaml.safe_load(programs_path.read_text(encoding="utf-8"))
    existing_ids = {p["id"] for p in existing}

    for prog in PROGRAMS:
        pid = prog["id"]

        # Rule file
        rule_key = pid
        if rule_key == "shuugyou_sokushin_teate":
            rule_key = "sai_shushoku_teate_koyou"
        rule_text = RULES_TPL.get(rule_key, RULES_TPL.get(pid, ""))
        if not rule_text:
            print(f"  SKIP {pid}: no rule template")
            continue
        if prog["layer"] == "national":
            rule_path = REPO / "rules" / "national" / f"{pid}.pl"
        else:
            rule_path = REPO / "rules" / "municipal" / prog["municipality"] / f"{pid}.pl"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(rule_text, encoding="utf-8")

        # Golden tests
        golden_dir = REPO / "tests" / "golden" / pid
        golden_dir.mkdir(parents=True, exist_ok=True)
        cases = []
        for c in prog["cases"]:
            case = {"name": c["name"], "as_of": "2026-06-15",
                    "municipality": "shibuya", "facts": c["facts"],
                    "expect": c["expect"]}
            cases.append(case)
        (golden_dir / "cases.yaml").write_text(
            yaml.dump(cases, allow_unicode=True, sort_keys=False), encoding="utf-8")
        statute_md = f"# {prog['name']}\n\n"
        for s in prog["statute"]:
            statute_md += f"- {s['ref']}: {s['url']}\n"
        (golden_dir / "statute_source.md").write_text(statute_md, encoding="utf-8")

        # programs.yaml
        if pid not in existing_ids:
            entry = {k: prog[k] for k in
                     ["id","name","layer","municipality","subject","unit","amount_type","potential_amount"]}
            entry["status"] = "supported"
            entry["statute"] = prog["statute"]
            existing.append(entry)
            existing_ids.add(pid)
            print(f"  + {pid}")
        else:
            # update status if unsupported
            for p in existing:
                if p["id"] == pid and p["status"] == "unsupported":
                    p["status"] = "supported"
                    p["statute"] = prog["statute"]
                    p["potential_amount"] = prog["potential_amount"]
                    print(f"  ^ {pid} (unsupported -> supported)")
                    break
            else:
                print(f"  = {pid} (exists)")

    programs_path.write_text(
        yaml.dump(existing, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8")
    print(f"\nDone. {len(PROGRAMS)} programs processed.")

if __name__ == "__main__":
    main()
