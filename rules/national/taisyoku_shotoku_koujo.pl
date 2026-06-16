:- module(taisyoku_shotoku_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, taisyoku_kin, "retirement benefit received") :-
    claimant(P), unknown(taisyoku_kin(P)).

kettei_status(P, self, ineligible(no_taisyoku_kin)) :-
    claimant(P), val(taisyoku_kin(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(taisyoku_koujo))) :-
    claimant(P), val(taisyoku_kin(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
