% ============================================================
% tokubetsu_shogaisha_teate.pl - Special Disability Allowance
% VERIFIED 2026-06-15: 28,840 JPY/month (R8). Age >= 20, severe
% disability (v1: shintai_1 only as proxy for detailed assessment).
% Income limit: 3,604,000 + 380,000 * dependents.
% Subject: claimant (self).
% Sources: tests/golden/tokubetsu_shogaisha_teate/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(tokubetsu_shogaisha_teate, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

tokusho_limit(N, L) :- integer(N), N >= 0, L is 3604000 + 380000 * N.

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).
required_fact(P, seikatsu_hogo, "public assistance") :-
    claimant(P), unknown(seikatsu_hogo(P)).
required_fact(P, income, "claimant income") :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, "exact income") :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    tokusho_limit(N, L), v_indet(V, L).

kettei_status(P, self, error(structural_facts_missing)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, ineligible(under_20)) :-
    claimant(P), age(P, A), A < 20, !.
kettei_status(P, self, ineligible(grade_not_covered)) :-
    claimant(P), val(shogai_techo(P), G), G \= shintai_1, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, ineligible(income_over)) :-
    claimant(P), val(shogai_techo(P), shintai_1),
    val(income(P), V), val(fuyou_ninzu(P), N),
    tokusho_limit(N, L), v_geq(V, L), !.
kettei_status(P, self, decided(monthly(28840))) :-
    claimant(P), val(shogai_techo(P), shintai_1),
    val(income(P), V), val(fuyou_ninzu(P), N),
    tokusho_limit(N, L), v_lt(V, L), !.
kettei_status(_, _, error(no_rule_matched)).
