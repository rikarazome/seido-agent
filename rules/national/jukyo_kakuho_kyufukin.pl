:- module(jukyo_kakuho_kyufukin, [kettei_status/3, required_fact/3]).

required_fact(P, rishoku, "rishoku status") :-
    claimant(P), unknown(rishoku(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(receiving_seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, ineligible(not_rishoku)) :-
    claimant(P), val(rishoku(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(jukyo_kakuho))) :-
    claimant(P), val(rishoku(P), true), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
