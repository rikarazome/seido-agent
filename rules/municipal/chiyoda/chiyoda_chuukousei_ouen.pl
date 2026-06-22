% chiyoda_chuukousei_ouen.pl - Chiyoda ward junior/senior high student support
% VERIFIED 2026-06-22: 15,000 JPY/month per child (ages 12-18).
% Source: https://www.city.chiyoda.lg.jp/koho/kosodate/teate/chukosei-oenteate.html

:- module(chiyoda_chuukousei_ouen, [kettei_status/3, required_fact/3]).

required_fact(_, _, _) :- fail.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C), \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(age_under_12)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A < 12, !.
kettei_status(P, C, ineligible(age_over_18)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 18, !.
kettei_status(P, C, decided(monthly(15000))) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 12, A < 18, !.
kettei_status(_, _, error(no_rule_matched)).
