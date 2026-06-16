:- module(saigai_gensai, [kettei_status/3, required_fact/3]).

required_fact(P, saigai_higai, "disaster/theft damage") :-
    claimant(P), unknown(saigai_higai(P)).

kettei_status(P, self, ineligible(no_damage)) :-
    claimant(P), val(saigai_higai(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(saigai_gensai))) :-
    claimant(P), val(saigai_higai(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
