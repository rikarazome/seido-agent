% ============================================================
% tokyo_jidou_ikusei_teate.pl - Tokyo Child Development Allowance
% (single-parent; implemented by wards). VERIFIED 2026-06-11:
% 13,500 JPY/month per child, claimant-only income limit
% 3,604,000 + 380,000 * dependents (linear, confirmed 0..5), no taper
% (full or nothing), de-facto-spouse exclusion as in jidou fuyou teate.
% v1 scope: elderly/specified-dependent additions to the limit are NOT
% modeled (goldens avoid such households) -- see
% tests/golden/tokyo_jidou_ikusei_teate/statute_source.md.
% Requires engine.pl.
% ============================================================

:- module(tokyo_jidou_ikusei_teate, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

taisho_jido(C) :-
    child(C), age_nendo_matsu(C, A), A =< 18.

jogai_confirmed(C, 'de-facto marriage (ordinance exclusion)') :-
    yes(seikei_douitsu_partner(C)).

% claimant-only income limit (no dependent-obligor test, no taper)
ikusei_limit(N, L) :- integer(N), N >= 0, L is 3604000 + 380000 * N.

required_fact(P, hitorioya, 'is the household single-parent') :-
    claimant(P), unknown(hitorioya(P)).
required_fact(P, hitorioya_jiyuu, 'statutory single-parent cause') :-
    claimant(P), yes(hitorioya(P)), unknown(hitorioya_jiyuu(P)).
required_fact(P, seikei_douitsu_partner, 'de-facto spouse cohabitation') :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    unknown(seikei_douitsu_partner(C)).
required_fact(P, income, 'income of claimant (after statutory deduction)') :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, 'number of tax dependents') :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, 'exact income (given range straddles the limit)') :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    ikusei_limit(N, L), v_indet(V, L).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('child past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    \+ taisho_jido(C), !.
kettei_status(P, C, ineligible('no single-parent cause')) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    no(hitorioya(P)), !.
kettei_status(P, C, ineligible(Reason)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    jogai_confirmed(C, Reason), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    \+ jogai_confirmed(C, _),
    findall(F, required_fact(P, F, _), Ms),
    sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, decided(monthly(13500))) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    yes(hitorioya(P)), val(hitorioya_jiyuu(P), _),
    no(seikei_douitsu_partner(C)),
    val(income(P), V), val(fuyou_ninzu(P), N),
    ikusei_limit(N, L), v_lt(V, L), !.
kettei_status(P, C, ineligible('income exceeds limit')) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    val(income(P), V), val(fuyou_ninzu(P), N),
    ikusei_limit(N, L), v_geq(V, L), !.
kettei_status(_, _, error(no_rule_matched)).
