:- module(kougaku_kaigo_service, [kettei_status/3, required_fact/3]).

required_fact(P, kaigo_nintei, "kaigo nintei level") :-
    claimant(P), unknown(kaigo_nintei(P)).

kettei_status(P, self, ineligible(no_kaigo_nintei)) :-
    claimant(P), val(kaigo_nintei(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(kougaku_kaigo))) :-
    claimant(P), val(kaigo_nintei(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
