:- module(seikatsu_hogo_seido, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "hikazei status") :-
    claimant(P), unknown(hikazei(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(not_eligible)) :-
    claimant(P), val(hikazei(P), false), !.
kettei_status(P, self, decided(kubun(seikatsu_hogo_annai))) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(seikatsu_hogo_soudan))) :-
    claimant(P), val(hikazei(P), true), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
