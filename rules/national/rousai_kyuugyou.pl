:- module(rousai_kyuugyou, [kettei_status/3, required_fact/3]).

required_fact(P, rousai, "work injury status") :-
    claimant(P), unknown(rousai(P)).

kettei_status(P, self, ineligible(no_rousai)) :-
    claimant(P), val(rousai(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(rousai_kyuugyou))) :-
    claimant(P), val(rousai(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
