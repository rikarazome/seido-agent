% ============================================================
% shibuya_birthday_support.pl - Shibuya Birthday Support (1st birthday)
% VERIFIED 2026-06-11: Amazon gift card; children born FY2025 get
% 100,000 JPY (FY2026-only special), born FY2023/FY2024 get 60,000 JPY.
% FY2026+ births: amount NOT yet announced (official) -- surfaced as an
% ineligible with that reason; updating this rule when announced is a
% live demo of the outer DevOps loop. Sources in
% tests/golden/shibuya_birthday_support/statute_source.md.
% Uses the birth_nendo/2 structural fact (birth fiscal year).
% Requires engine.pl.
% ============================================================

:- module(shibuya_birthday_support, [kettei_status/3, required_fact/3]).

% no askable facts: birth fiscal year and age are structural
required_fact(_, _, _) :- fail.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    ( \+ age(C, _) ; \+ birth_nendo(C, _) ), !.
kettei_status(P, C, ineligible('past the 1st-birthday support window')) :-
    claimant(P), kango_by(C, P),
    age(C, A), A >= 2, !.
kettei_status(P, C, decided(oneoff(100000))) :-
    claimant(P), kango_by(C, P),
    birth_nendo(C, 2025), !.       % FY2026-only special amount
kettei_status(P, C, decided(oneoff(60000))) :-
    claimant(P), kango_by(C, P),
    birth_nendo(C, Y), (Y == 2023 ; Y == 2024), !.
kettei_status(P, C, ineligible('grant for children born FY2026+ not yet announced (as of 2026-06)')) :-
    claimant(P), kango_by(C, P),
    birth_nendo(C, Y), Y >= 2026, !.
kettei_status(P, C, ineligible('born before FY2023 (program start)')) :-
    claimant(P), kango_by(C, P),
    birth_nendo(C, Y), Y < 2023, !.
kettei_status(_, _, error(no_rule_matched)).
