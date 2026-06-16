:- module(iryouhi_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, iryouhi_10man, "medical expenses over 100k") :-
    claimant(P), unknown(iryouhi_10man(P)).

kettei_status(P, self, ineligible(under_10man)) :-
    claimant(P), val(iryouhi_10man(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(iryouhi_koujo))) :-
    claimant(P), val(iryouhi_10man(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
