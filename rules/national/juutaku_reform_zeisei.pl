:- module(juutaku_reform_zeisei, [kettei_status/3, required_fact/3]).

required_fact(P, juutaku_kaishu, "housing renovation") :-
    claimant(P), unknown(juutaku_kaishu(P)).

kettei_status(P, self, ineligible(no_renovation)) :-
    claimant(P), val(juutaku_kaishu(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(reform_zeisei))) :-
    claimant(P), val(juutaku_kaishu(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
