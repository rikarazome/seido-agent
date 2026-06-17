% nerima_dai3shi_ouen.pl - Nerima 3rd child birth celebration
% VERIFIED 2026-06-17. Subject: child. 3rd child or later, age 0.
% Amount: 100,000 JPY (oneoff). Source: nerima official page.
% Requires engine.pl.

:- module(nerima_dai3shi_ouen, [kettei_status/3, required_fact/3]).

required_fact(_, _, _) :- fail.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C), \+ age(C, _), !.
kettei_status(P, C, ineligible(age_over)) :-
    claimant(P), kango_by(C, P), child(C),
    age(C, A), A > 0, !.
kettei_status(P, C, ineligible(not_3rd_child)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(K, (child(K), kango_by(K, P)), Kids),
    length(Kids, N), N < 3, !.
kettei_status(P, C, decided(oneoff(100000))) :-
    claimant(P), kango_by(C, P), child(C), !.
kettei_status(_, _, error(no_rule_matched)).
