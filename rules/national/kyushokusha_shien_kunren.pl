:- module(kyushokusha_shien_kunren, [kettei_status/3, required_fact/3]).

required_fact(P, rishoku, "rishoku status") :-
    claimant(P), unknown(rishoku(P)).
required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).

kettei_status(P, self, ineligible(not_rishoku)) :-
    claimant(P), val(rishoku(P), false), !.
kettei_status(P, self, ineligible(has_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(amount(100000))) :-
    claimant(P), val(rishoku(P), true), val(koyou_hoken(P), false), !.
kettei_status(_, _, error(no_rule_matched)).
