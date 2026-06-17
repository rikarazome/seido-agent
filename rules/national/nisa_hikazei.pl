:- module(nisa_hikazei, [kettei_status/3]).
:- discontiguous required_fact/3.

kettei_status(P, self, decided(kubun(nisa_info))) :-
    claimant(P), !.
kettei_status(_, _, error(no_rule_matched)).
