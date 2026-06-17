% kokumin_nenkin_menjo - National Pension Premium Exemption
% Source: 国民年金法90条・90条の2
% zenmen/yuuyo: (N+1)*35万+32万, 3/4: 88万+38万*N, half: 128万+38万*N, 1/4: 168万+38万*N
% N = fuyou_ninzu. 38万 per dependent is approximate (扶養控除額).
:- module(kokumin_nenkin_menjo, [kettei_status/3, required_fact/3]).

zenmen_limit(N, L) :- integer(N), N >= 0, L is (N + 1) * 350000 + 320000.
menjo34_limit(N, L) :- integer(N), N >= 0, L is 880000 + 380000 * N.
menjo_half_limit(N, L) :- integer(N), N >= 0, L is 1280000 + 380000 * N.
menjo14_limit(N, L) :- integer(N), N >= 0, L is 1680000 + 380000 * N.

required_fact(P, income, "income") :-
    claimant(P), unknown(income(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), val(income(P), _), unknown(fuyou_ninzu(P)).

kettei_status(P, self, ineligible(receiving_seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(zenmen))) :-
    claimant(P), val(income(P), I), val(fuyou_ninzu(P), N),
    zenmen_limit(N, L), v_lt(I, L), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_3_4))) :-
    claimant(P), val(income(P), I), val(fuyou_ninzu(P), N),
    menjo34_limit(N, L), v_lt(I, L), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_half))) :-
    claimant(P), val(income(P), I), val(fuyou_ninzu(P), N),
    menjo_half_limit(N, L), v_lt(I, L), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_1_4))) :-
    claimant(P), val(income(P), I), val(fuyou_ninzu(P), N),
    menjo14_limit(N, L), v_lt(I, L), no(seikatsu_hogo(P)), !.
kettei_status(P, self, ineligible(income_exceeds_limit)) :-
    claimant(P), val(income(P), _), val(fuyou_ninzu(P), _), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
