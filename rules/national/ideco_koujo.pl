:- module(ideco_koujo, [kettei_status/3]).
:- discontiguous required_fact/3.

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, ineligible(under_20)) :-
    claimant(P), age(P, A), A < 20, !.
kettei_status(P, self, ineligible(over_65)) :-
    claimant(P), age(P, A), A >= 65, !.
kettei_status(P, self, decided(kubun(ideco_koujo))) :-
    claimant(P), age(P, A), A >= 20, A < 65, !.
kettei_status(_, _, error(no_rule_matched)).
