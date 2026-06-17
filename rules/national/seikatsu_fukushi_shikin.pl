:- module(seikatsu_fukushi_shikin, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, self, ineligible(not_low_income)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(kinkyuu_koguchi))) :-
    claimant(P), val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
