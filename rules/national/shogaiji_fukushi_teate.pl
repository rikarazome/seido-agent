% ============================================================
% shogaiji_fukushi_teate.pl - Disabled Child Welfare Allowance
% VERIFIED 2026-06-15: 15,690 JPY/month (R8). Child under 20,
% severe disability requiring constant care.
% v1: shintai_1 only as proxy for detailed severity assessment.
% Income limit: 4,596,000 + 380,000 * N (obligor income).
% Subject: child. Uses per-child shogai_techo_child.
% Sources: tests/golden/shogaiji_fukushi_teate/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(shogaiji_fukushi_teate, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

shofuku_limit(N, L) :- integer(N), N >= 0, L is 4596000 + 380000 * N.

required_fact(P, shogai_techo_child, "child disability certificate") :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A < 20,
    unknown(shogai_techo_child(C)).
required_fact(P, income, "obligor income") :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, "exact income") :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    shofuku_limit(N, L), v_indet(V, L).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_20_or_over)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 20, !.
kettei_status(P, C, ineligible(grade_not_covered)) :-
    claimant(P), kango_by(C, P), child(C),
    val(shogai_techo_child(C), G), G \= shintai_1, !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, ineligible(income_over)) :-
    claimant(P), kango_by(C, P), child(C),
    val(shogai_techo_child(C), shintai_1),
    val(income(P), V), val(fuyou_ninzu(P), N),
    shofuku_limit(N, L), v_geq(V, L), !.
kettei_status(P, C, decided(monthly(16560))) :-
    claimant(P), kango_by(C, P), child(C),
    val(shogai_techo_child(C), shintai_1),
    val(income(P), V), val(fuyou_ninzu(P), N),
    shofuku_limit(N, L), v_lt(V, L), !.
kettei_status(_, _, error(no_rule_matched)).
