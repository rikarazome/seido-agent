:- module(shoubyou_teatekin, [kettei_status/3, required_fact/3]).

required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), unknown(hoken_shubetsu(P)).
required_fact(P, byouki_kyugyou, "sick leave status") :-
    claimant(P), unknown(byouki_kyugyou(P)).

kettei_status(P, self, ineligible(not_shakai_hoken)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \= shakai_hoken, !.
kettei_status(P, self, ineligible(not_byouki_kyugyou)) :-
    claimant(P), val(byouki_kyugyou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(shoubyou_teate))) :-
    claimant(P), val(hoken_shubetsu(P), shakai_hoken), val(byouki_kyugyou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
