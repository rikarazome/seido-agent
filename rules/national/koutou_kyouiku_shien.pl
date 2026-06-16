:- module(koutou_kyouiku_shien, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, daigaku_zaigaku, "university enrollment") :-
    claimant(P), unknown(daigaku_zaigaku(P)).

kettei_status(P, self, ineligible(not_hikazei)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, ineligible(not_enrolled)) :-
    claimant(P), val(daigaku_zaigaku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(jugyo_menjo))) :-
    claimant(P), val(hikazei(P), true), val(daigaku_zaigaku(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
