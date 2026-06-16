:- module(sanzen_sango_nenkin_menjo, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), val(ninshin(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(menjo_4months))) :-
    claimant(P), val(ninshin(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
