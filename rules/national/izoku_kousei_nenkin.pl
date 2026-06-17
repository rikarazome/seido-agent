:- module(izoku_kousei_nenkin, [kettei_status/3, required_fact/3]).

required_fact(P, haiguusha_shibou, "spouse death") :-
    claimant(P), unknown(haiguusha_shibou(P)).

kettei_status(P, self, ineligible(no_spouse_death)) :-
    claimant(P), val(haiguusha_shibou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(izoku_kousei))) :-
    claimant(P), val(haiguusha_shibou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
