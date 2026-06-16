:- module(nichijou_seikatsu_yougu, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(yougu_kyufu))) :-
    claimant(P), val(shogai_techo(P), G), G \= nashi, !.
kettei_status(_, _, error(no_rule_matched)).
