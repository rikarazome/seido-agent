% ============================================================
% shiritsu_koko_jugyoryo_keigen.pl - Tokyo Private HS Tuition Reduction
% VERIFIED 2026-06-15: up to 484,000 JPY/year (diff between national
% support and tuition cap). Income limit ABOLISHED 2026-04.
% Conditions: Tokyo resident + enrolled in private high school.
% FY-end age <= 19 (normal HS range + 1 year margin for repeaters).
% Sources: tests/golden/shiritsu_koko_jugyoryo_keigen/statute_source.md
% Uses PER-CHILD askables: koukou_zaigaku, gakkou_kubun.
% Requires engine.pl.
% ============================================================

:- module(shiritsu_koko_jugyoryo_keigen, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

required_fact(P, koukou_zaigaku, "high school enrollment") :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A =< 19,
    unknown(koukou_zaigaku(C)).
required_fact(P, gakkou_kubun, "school type") :-
    claimant(P), kango_by(C, P), child(C),
    yes(koukou_zaigaku(C)), unknown(gakkou_kubun(C)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_over)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A > 19, !.
kettei_status(P, C, ineligible(not_in_high_school)) :-
    claimant(P), kango_by(C, P), child(C),
    no(koukou_zaigaku(C)), !.
kettei_status(P, C, ineligible(not_private_school)) :-
    claimant(P), kango_by(C, P), child(C),
    yes(koukou_zaigaku(C)), val(gakkou_kubun(C), kouritsu), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, decided(yearly(484000))) :-
    claimant(P), kango_by(C, P), child(C),
    yes(koukou_zaigaku(C)), val(gakkou_kubun(C), shiritsu), !.
kettei_status(_, _, error(no_rule_matched)).
