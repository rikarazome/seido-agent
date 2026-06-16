:- module(shougai_kiso_nenkin, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

taisho_toukyu(shintai_1).
taisho_toukyu(shintai_2).
taisho_toukyu(seishin_1).
taisho_toukyu(seishin_2).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, ineligible(grade_not_covered)) :-
    claimant(P), val(shogai_techo(P), G), \+ taisho_toukyu(G), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(kiso_1kyu))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_1 ; G = seishin_1), !.
kettei_status(P, self, decided(kubun(kiso_2kyu))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_2 ; G = seishin_2), !.
kettei_status(_, _, error(no_rule_matched)).
