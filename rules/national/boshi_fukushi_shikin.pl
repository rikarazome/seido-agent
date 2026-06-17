:- module(boshi_fukushi_shikin, [kettei_status/3, required_fact/3]).

required_fact(P, hitorioya, "hitorioya status") :-
    claimant(P), unknown(hitorioya(P)).

kettei_status(P, self, ineligible(not_hitorioya)) :-
    claimant(P), val(hitorioya(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(boshi_kashitsuke))) :-
    claimant(P), val(hitorioya(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
