"""Generate per-ward kodomo-iryouhi artifacts from the verified source table.

This is the "turn the crank" pipeline for the 23-ward expansion:
  data/ward_iryouhi_sources.yaml  (research-verified, primary sources only)
    -> rules/municipal/<ward>/<ward>_kodomo_iryouhi.pl   (from shibuya template)
    -> tests/golden/<ward>_kodomo_iryouhi/{statute_source.md, cases.yaml}
    -> data/programs.yaml entry (status: supported)

Idempotent: generated rule/golden files are overwritten (they are derived
artifacts; the source of truth is the YAML table + the shibuya template),
programs.yaml entries are appended only when the id is absent.

Run from repo root:  python scripts/gen_ward_iryouhi.py
"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "data" / "ward_iryouhi_sources.yaml"
PROGRAMS = REPO / "data" / "programs.yaml"

RULE_TEMPLATE = """% ============================================================
% {pid}.pl - {ward} ward child medical cost subsidy
% VERIFIED {verified}: in-kind benefit (insured co-payment covered),
% age 0 to FY-end of 18, public health insurance required, no income
% test. Generated from the shibuya template by
% scripts/gen_ward_iryouhi.py -- do not edit by hand; source fixation
% in tests/golden/{pid}/statute_source.md.
% Ward residence is implied by the form's municipality selection.
% Requires engine.pl.
% ============================================================

:- module({pid}, [kettei_status/3, required_fact/3]).

required_fact(P, kenkou_hoken, 'is the household covered by public health insurance') :-
    claimant(P), unknown(kenkou_hoken(P)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \\+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A > 18, !.
kettei_status(P, C, ineligible('not covered by public health insurance')) :-
    claimant(P), kango_by(C, P),
    no(kenkou_hoken(P)), !.
kettei_status(P, C, blocked([kenkou_hoken])) :-
    claimant(P), kango_by(C, P),
    unknown(kenkou_hoken(P)), !.
kettei_status(P, C, decided(in_kind(jiko_futan_josei))) :-
    claimant(P), kango_by(C, P),
    yes(kenkou_hoken(P)), !.
kettei_status(_, _, error(no_rule_matched)).
"""

CASES_TEMPLATE = """\
# 子ども医療費助成（{name_ja}） golden cases（statute_source.md）
# scripts/gen_ward_iryouhi.py が生成（渋谷区テンプレートと同一意味論）
# 区内在住は居住自治体選択から暗黙充足。健康保険加入は世帯レベルaskable

- name: {ward}_ki_insured_decided
  as_of: "2026-06-12"
  facts:
    claimant: {{ birth_date: "1988-04-01" }}
    children: [ {{ id: c1, birth_date: "2019-06-01" }} ]
    askable: {{ kenkou_hoken: true }}
  expect: {{ subject: c1, status: decided, detail: "in_kind(jiko_futan_josei)" }}

- name: {ward}_ki_insurance_unknown_blocks
  as_of: "2026-06-12"
  facts:
    claimant: {{ birth_date: "1988-04-01" }}
    children: [ {{ id: c1, birth_date: "2019-06-01" }} ]
    askable: {{ kenkou_hoken: null }}
  expect: {{ subject: c1, status: blocked, detail: "[kenkou_hoken]" }}

- name: {ward}_ki_uninsured_ineligible
  as_of: "2026-06-12"
  facts:
    claimant: {{ birth_date: "1988-04-01" }}
    children: [ {{ id: c1, birth_date: "2019-06-01" }} ]
    askable: {{ kenkou_hoken: false }}
  expect: {{ subject: c1, status: ineligible,
            detail: "'not covered by public health insurance'" }}

- name: {ward}_ki_overage_ineligible
  as_of: "2026-06-12"
  facts:
    claimant: {{ birth_date: "1980-01-01" }}
    children: [ {{ id: c1, birth_date: "2006-09-01" }} ]   # FY-end 20
    askable: {{ kenkou_hoken: true }}
  expect: {{ subject: c1, status: ineligible, detail: "'past FY-end age 18'" }}
"""

STATUTE_TEMPLATE = """\
# 子ども医療費助成（{name_ja}） — 出典固定

**状態: VERIFIED（{verified}、並列リサーチエージェントによる公式一次情報調査）**

| 項目 | 確定値 |
|---|---|
| 対象年齢 | 0歳〜18歳年度末（マル乳/マル子/マル青で連続カバー） |
| 助成内容 | 保険診療の自己負担分を助成 |
| 要件 | 区内在住 + 日本の健康保険加入 |
| 所得制限 | なし |

出典:
- {ref}: {url}

{note_block}意味論は渋谷区テンプレート（tests/golden/shibuya_kodomo_iryouhi/）と同一。
このファイルと cases.yaml・ルールは scripts/gen_ward_iryouhi.py が
data/ward_iryouhi_sources.yaml から生成する（手編集しない）。
区内在住はフォームの居住自治体選択から暗黙に充足。
"""

PROGRAM_ENTRY = """
- id: {pid}
  name: 子ども医療費助成
  layer: municipal
  municipality: {ward}
  subject: child
  unit: per_child
  amount_type: in_kind
  potential_amount: null         # 現物給付（自己負担分助成）のため金額表示なし
  status: supported
  statute:
    - {{ ref: "{ref}", url: "{url}" }}
"""


def _write(path: Path, text: str) -> None:
    # Path.write_text(newline=...) requires 3.10; local dev runs 3.9
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main() -> None:
    wards = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    existing = {p["id"] for p in
                yaml.safe_load(PROGRAMS.read_text(encoding="utf-8"))}
    appended = []
    for w in wards:
        ward, pid = w["id"], f"{w['id']}_kodomo_iryouhi"
        rule_dir = REPO / "rules" / "municipal" / ward
        golden_dir = REPO / "tests" / "golden" / pid
        rule_dir.mkdir(parents=True, exist_ok=True)
        golden_dir.mkdir(parents=True, exist_ok=True)

        _write(rule_dir / f"{pid}.pl",
               RULE_TEMPLATE.format(pid=pid, ward=ward,
                                    verified=w["verified"]))
        _write(golden_dir / "cases.yaml",
               CASES_TEMPLATE.format(ward=ward, name_ja=w["name_ja"]))
        note_block = f"注意: {w['note']}\n\n" if w.get("note") else ""
        _write(golden_dir / "statute_source.md",
               STATUTE_TEMPLATE.format(name_ja=w["name_ja"], ref=w["ref"],
                                       url=w["url"], verified=w["verified"],
                                       note_block=note_block))

        if pid not in existing:
            with PROGRAMS.open("a", encoding="utf-8", newline="\n") as f:
                f.write(PROGRAM_ENTRY.format(pid=pid, ward=ward,
                                             ref=w["ref"], url=w["url"]))
            appended.append(pid)
    print(f"generated {len(wards)} wards; appended {len(appended)} "
          f"programs.yaml entries: {appended}")


if __name__ == "__main__":
    main()
