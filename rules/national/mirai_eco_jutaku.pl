:- module(mirai_eco_jutaku, [kettei_status/3, required_fact/3]).

required_fact(P, jutaku_shinchiku, "housing construction") :-
    claimant(P), unknown(jutaku_shinchiku(P)).

kettei_status(P, self, ineligible(no_construction)) :-
    claimant(P), val(jutaku_shinchiku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(mirai_eco))) :-
    claimant(P), val(jutaku_shinchiku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
