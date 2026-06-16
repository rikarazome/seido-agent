:- module(seimei_hoken_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, seimei_hoken, "life insurance enrollment") :-
    claimant(P), unknown(seimei_hoken(P)).

kettei_status(P, self, ineligible(no_seimei_hoken)) :-
    claimant(P), val(seimei_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(seimei_hoken_koujo))) :-
    claimant(P), val(seimei_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
