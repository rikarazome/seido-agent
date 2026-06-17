% WARNING: Income thresholds are for SINGLE-PERSON household only.
% Correct formula: 7wari=43万, 5wari=43万+29.5万*N, 2wari=43万+54.5万*N
% This rule is unsupported and must not be marked supported without rewrite.
:- module(kokuho_keigen, [kettei_status/3, required_fact/3]).

required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), unknown(hoken_shubetsu(P)).
required_fact(P, income, "income") :-
    claimant(P), val(hoken_shubetsu(P), kokuho), unknown(income(P)).

kettei_status(P, self, ineligible(not_kokuho)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \= kokuho, !.
kettei_status(P, self, ineligible(income_exceeds_limit)) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), v_geq(I, 3000001), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(keigen_7wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), v_lt(I, 430001), !.
kettei_status(P, self, decided(kubun(keigen_5wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), v_lt(I, 1050001), !.
kettei_status(P, self, decided(kubun(keigen_2wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), v_lt(I, 3000001), !.
kettei_status(_, _, error(no_rule_matched)).
