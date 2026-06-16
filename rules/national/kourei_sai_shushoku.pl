:- module(kourei_sai_shushoku, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, rishoku, "rishoku status") :-
    claimant(P), unknown(rishoku(P)).

kettei_status(P, self, error(structural_no_age)) :-
    claimant(P), \+ age(P, _), !.
kettei_status(P, self, ineligible(under_60)) :-
    claimant(P), age(P, A), A < 60, !.
kettei_status(P, self, ineligible(over_65)) :-
    claimant(P), age(P, A), A >= 65, !.
kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_rishoku)) :-
    claimant(P), val(rishoku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(kourei_sai_shushoku))) :-
    claimant(P), age(P, A), A >= 60, A < 65,
    val(koyou_hoken(P), true), val(rishoku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
