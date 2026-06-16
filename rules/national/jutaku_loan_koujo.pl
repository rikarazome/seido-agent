:- module(jutaku_loan_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, jutaku_loan, "housing loan") :-
    claimant(P), unknown(jutaku_loan(P)).

kettei_status(P, self, ineligible(no_jutaku_loan)) :-
    claimant(P), val(jutaku_loan(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(jutaku_loan_koujo))) :-
    claimant(P), val(jutaku_loan(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
