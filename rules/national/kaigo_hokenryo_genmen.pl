:- module(kaigo_hokenryo_genmen, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), age(P, A), A >= 65, unknown(hikazei(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, ineligible(under_65)) :-
    claimant(P), age(P, A), A < 65, !.
kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), age(P, A), A >= 65, val(hikazei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), age(P, A), A >= 65,
    findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(genmen))) :-
    claimant(P), age(P, A), A >= 65, val(hikazei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
