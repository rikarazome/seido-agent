:- module(silver_pass, [kettei_status/3]).
:- discontiguous required_fact/3.

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, ineligible(under_70)) :-
    claimant(P), age(P, A), A < 70, !.
kettei_status(P, self, decided(kubun(silver_pass))) :-
    claimant(P), age(P, A), A >= 70, !.
kettei_status(_, _, error(no_rule_matched)).
