:- module(kaigo_kyuugyou_kyufu, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, kaigo_family, "family caregiving status") :-
    claimant(P), unknown(kaigo_family(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_kaigo)) :-
    claimant(P), val(kaigo_family(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(kaigo_kyuugyou))) :-
    claimant(P), val(koyou_hoken(P), true), val(kaigo_family(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
