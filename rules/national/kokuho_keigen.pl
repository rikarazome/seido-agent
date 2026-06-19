% kokuho_keigen - National Health Insurance Premium Reduction (7/5/2 wari)
% Source: NHI Act Art.81, Enforcement Order Art.29-7
% Formula: 7wari<=430000, 5wari<=430000+295000*(N+1), 2wari<=430000+545000*(N+1)
% N = fuyou_ninzu (proxy for NHI insured count; differs if household head is on employer insurance)
:- module(kokuho_keigen, [kettei_status/3, required_fact/3]).

keigen_limit_5(N, L) :- integer(N), N >= 0, L is 430000 + 295000 * (N + 1).
keigen_limit_2(N, L) :- integer(N), N >= 0, L is 430000 + 545000 * (N + 1).

required_fact(P, hoken_shubetsu, "health insurance type") :-
    claimant(P), unknown(hoken_shubetsu(P)).
required_fact(P, income, "income") :-
    claimant(P), val(hoken_shubetsu(P), kokuho), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), \+ v_lt(I, 430001),
    unknown(fuyou_ninzu(P)).

kettei_status(P, self, ineligible(not_kokuho)) :-
    claimant(P), val(hoken_shubetsu(P), T), T \= kokuho, !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(keigen_7wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), v_lt(I, 430001), !.
kettei_status(P, self, decided(kubun(keigen_5wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), val(fuyou_ninzu(P), N),
    keigen_limit_5(N, L5), v_lt(I, L5), !.
kettei_status(P, self, decided(kubun(keigen_2wari))) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), val(fuyou_ninzu(P), N),
    keigen_limit_2(N, L2), v_lt(I, L2), !.
kettei_status(P, self, ineligible(income_exceeds_limit)) :-
    claimant(P), val(hoken_shubetsu(P), kokuho),
    val(income(P), I), val(fuyou_ninzu(P), N),
    keigen_limit_2(N, L2), v_geq(I, L2), !.
kettei_status(_, _, error(no_rule_matched)).
