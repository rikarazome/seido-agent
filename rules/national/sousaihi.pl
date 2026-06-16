:- module(sousaihi, [kettei_status/3, required_fact/3]).

required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), unknown(hoken_shubetsu(P)).

kettei_status(P, self, ineligible(not_kokuho)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \= kokuho, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(amount(70000))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho), !.
kettei_status(_, _, error(no_rule_matched)).
