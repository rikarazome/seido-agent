% ============================================================
% jiritsu_shien_iryo_ikusei.pl - Self-reliance Medical Support (Growth)
% VERIFIED 2026-06-15: in-kind (copay 10%) for children under 18
% with physical disability. No income limit for eligibility.
% v1: shintai_* as proxy (shintai_1/2/3 all eligible).
% Subject: child. Uses per-child shogai_techo_child.
% Sources: tests/golden/jiritsu_shien_iryo_ikusei/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(jiritsu_shien_iryo_ikusei, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

taisho_shintai(shintai_1).
taisho_shintai(shintai_2).
taisho_shintai(shintai_3).

required_fact(P, shogai_techo_child, "child disability certificate") :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A < 18,
    unknown(shogai_techo_child(C)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_18_or_over)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 18, !.
kettei_status(P, C, ineligible(not_physical_disability)) :-
    claimant(P), kango_by(C, P), child(C),
    val(shogai_techo_child(C), G), \+ taisho_shintai(G), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, decided(in_kind)) :-
    claimant(P), kango_by(C, P), child(C),
    val(shogai_techo_child(C), G), taisho_shintai(G), !.
kettei_status(_, _, error(no_rule_matched)).
