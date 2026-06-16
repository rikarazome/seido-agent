:- module(self_medication, [kettei_status/3, required_fact/3]).

required_fact(P, iryouhi_10man, "medical expenses check") :-
    claimant(P), unknown(iryouhi_10man(P)).

kettei_status(P, self, ineligible(iryouhi_koujo_available)) :-
    claimant(P), val(iryouhi_10man(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(self_medication))) :-
    claimant(P), val(iryouhi_10man(P), false), !.
kettei_status(_, _, error(no_rule_matched)).
