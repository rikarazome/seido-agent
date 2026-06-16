:- module(haiguusha_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, haiguusha, "spouse status") :-
    claimant(P), unknown(haiguusha(P)).

kettei_status(P, self, ineligible(no_haiguusha)) :-
    claimant(P), val(haiguusha(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(haiguusha_koujo))) :-
    claimant(P), val(haiguusha(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
