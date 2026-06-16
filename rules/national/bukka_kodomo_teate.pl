:- module(bukka_kodomo_teate, [kettei_status/3, required_fact/3]).
:- discontiguous required_fact/3.

kettei_status(_, C, ineligible(no_child)) :-
    \+ child(C), !.
kettei_status(_, C, decided(amount(20000))) :-
    child(C), !.
kettei_status(_, _, error(no_rule_matched)).
