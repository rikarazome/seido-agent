% ============================================================
% koto_shokugyo_kunren.pl - Higher Vocational Training Promotion Benefit
% VERIFIED 2026-06-15: 100,000 JPY/month (non-taxable) or 70,500
% (taxable). Single-parent, income limit per jidou_fuyou_teate
% zenbu limit: 1,490,000 + 380,000 * N.
% v1: training enrollment not modeled (shown as note on card).
% Subject: claimant (self). Must have child.
% Sources: tests/golden/koto_shokugyo_kunren/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(koto_shokugyo_kunren, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

has_child(P) :-
    claimant(P), kango_by(C, P), child(C), !.

kunren_limit(N, L) :- integer(N), N >= 0, L is 1490000 + 380000 * N.

required_fact(P, hitorioya, "single parent") :-
    claimant(P), unknown(hitorioya(P)).
required_fact(P, hikazei, "non-taxable household") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, income, "income") :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, "exact income") :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    kunren_limit(N, L), v_indet(V, L).

kettei_status(P, self, ineligible(no_child)) :-
    claimant(P), \+ has_child(P), !.
kettei_status(P, self, ineligible(not_single_parent)) :-
    claimant(P), no(hitorioya(P)), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, ineligible(income_over)) :-
    claimant(P), yes(hitorioya(P)),
    val(income(P), V), val(fuyou_ninzu(P), N),
    kunren_limit(N, L), v_geq(V, L), !.
kettei_status(P, self, decided(monthly(100000))) :-
    claimant(P), yes(hitorioya(P)), yes(hikazei(P)),
    val(income(P), V), val(fuyou_ninzu(P), N),
    kunren_limit(N, L), v_lt(V, L), !.
kettei_status(P, self, decided(monthly(70500))) :-
    claimant(P), yes(hitorioya(P)), no(hikazei(P)),
    val(income(P), V), val(fuyou_ninzu(P), N),
    kunren_limit(N, L), v_lt(V, L), !.
kettei_status(_, _, error(no_rule_matched)).
