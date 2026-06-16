:- module(jishin_hoken_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, jishin_hoken, "earthquake insurance") :-
    claimant(P), unknown(jishin_hoken(P)).

kettei_status(P, self, ineligible(no_jishin_hoken)) :-
    claimant(P), val(jishin_hoken(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(jishin_hoken_koujo))) :-
    claimant(P), val(jishin_hoken(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
