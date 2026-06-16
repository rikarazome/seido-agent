:- module(nhk_menjo, [kettei_status/3, required_fact/3]).

required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).
required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), no(seikatsu_hogo(P)), unknown(shogai_techo(P)).
required_fact(P, hikazei, "hikazei status") :-
    claimant(P), no(seikatsu_hogo(P)), unknown(hikazei(P)).

kettei_status(P, self, decided(kubun(zenmen_seiho))) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, decided(kubun(zenmen_shougai))) :-
    claimant(P), val(shogai_techo(P), G), G \= nashi,
    val(hikazei(P), true), !.
kettei_status(P, self, ineligible(not_eligible)) :-
    claimant(P), no(seikatsu_hogo(P)),
    (val(shogai_techo(P), nashi) ; (val(shogai_techo(P), _), val(hikazei(P), false))), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(_, _, error(no_rule_matched)).
