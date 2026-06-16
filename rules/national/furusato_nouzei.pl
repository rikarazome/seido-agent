:- module(furusato_nouzei, [kettei_status/3, required_fact/3]).

required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(furusato_nouzei))) :-
    claimant(P), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
