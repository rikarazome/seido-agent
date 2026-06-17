% WARNING: Income thresholds in this rule are INCORRECT.
% Correct values depend on dependents: zenmen=(N+1)*35+32, 3/4=88+deductions, etc.
% This rule is unsupported and must not be marked supported without rewrite.
:- module(kokumin_nenkin_menjo, [kettei_status/3, required_fact/3]).

required_fact(P, income, "income") :-
    claimant(P), unknown(income(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(receiving_seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, ineligible(income_exceeds_limit)) :-
    claimant(P), val(income(P), I), v_geq(I, 3600001), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(zenmen))) :-
    claimant(P), val(income(P), I), v_lt(I, 670001), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_3_4))) :-
    claimant(P), val(income(P), I), v_lt(I, 1180001), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_half))) :-
    claimant(P), val(income(P), I), v_lt(I, 1680001), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(menjo_1_4))) :-
    claimant(P), val(income(P), I), v_lt(I, 2280001), no(seikatsu_hogo(P)), !.
kettei_status(P, self, decided(kubun(yuuyo))) :-
    claimant(P), val(income(P), I), v_lt(I, 3600001), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
