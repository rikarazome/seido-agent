:- module(shogaisha_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, shogai_techo, "disability certificate") :-
    claimant(P), unknown(shogai_techo(P)).

kettei_status(P, self, ineligible(no_shogai_techo)) :-
    claimant(P), val(shogai_techo(P), nashi), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(tokubetsu_shogaisha))) :-
    claimant(P), val(shogai_techo(P), G), (G = shintai_1 ; G = shintai_2 ; G = seishin_1), !.
kettei_status(P, self, decided(kubun(ippan_shogaisha))) :-
    claimant(P), val(shogai_techo(P), _), !.
kettei_status(_, _, error(no_rule_matched)).
