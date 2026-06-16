:- module(shussan_teatekin, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).
required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), val(ninshin(P), true), unknown(hoken_shubetsu(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), val(ninshin(P), false), !.
kettei_status(P, self, ineligible(not_shakai_hoken)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \= shakai_hoken, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(shussan_teate))) :-
    claimant(P), val(ninshin(P), true), val(hoken_shubetsu(P), shakai_hoken), !.
kettei_status(_, _, error(no_rule_matched)).
