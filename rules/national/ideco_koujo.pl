:- module(ideco_koujo, [kettei_status/3]).
:- discontiguous required_fact/3.

kettei_status(P, self, decided(kubun(ideco_koujo))) :-
    claimant(P), !.
kettei_status(_, _, error(no_rule_matched)).
