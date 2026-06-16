:- module(maisouryou, [kettei_status/3, required_fact/3]).

required_fact(P, kenkou_hoken, "health insurance") :-
    claimant(P), unknown(kenkou_hoken(P)).

kettei_status(P, self, ineligible(no_kenkou_hoken)) :-
    claimant(P), val(kenkou_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(amount(50000))) :-
    claimant(P), val(kenkou_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
