% shounimansei_iryo_josei.pl - Child chronic disease medical subsidy
% VERIFIED 2026-06-15: in-kind. FY-end age < 18. No income limit
% for eligibility (copay caps vary). Subject: child.
% Requires engine.pl.

:- module(shounimansei_iryo_josei, [kettei_status/3, required_fact/3]).

required_fact(_, _, _) :- fail.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C), \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_over)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 18, !.
kettei_status(P, C, decided(in_kind)) :-
    claimant(P), kango_by(C, P), child(C), !.
kettei_status(_, _, error(no_rule_matched)).
