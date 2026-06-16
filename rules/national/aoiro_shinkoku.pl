:- module(aoiro_shinkoku, [kettei_status/3, required_fact/3]).

required_fact(P, jiei_gyou, "self-employed status") :-
    claimant(P), unknown(jiei_gyou(P)).

kettei_status(P, self, ineligible(not_self_employed)) :-
    claimant(P), val(jiei_gyou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(aoiro_65man))) :-
    claimant(P), val(jiei_gyou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
