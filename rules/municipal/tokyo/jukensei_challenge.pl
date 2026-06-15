% ============================================================
% jukensei_challenge.pl - Exam Challenge Support Loan (Tokyo)
% VERIFIED 2026-06-15: up to 200,000 JPY (cram school fees).
% Repayment waived on enrollment (de facto grant).
% Target: children at FY-end age 14-15 (chu3) or 17-18 (ko3).
% Income limit: approx 2,322,000 + 490,000 * N (converted from
% published household income thresholds via salary_to_shotoku).
% Subject: child.
% Sources: tests/golden/jukensei_challenge/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(jukensei_challenge, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

% chu3 (FY-end 14-15) or ko3 (FY-end 17-18)
target_grade(C) :-
    child(C), age_nendo_matsu(C, A),
    (  (A >= 14, A =< 15)
    ;  (A >= 17, A =< 18)
    ).

juken_limit(N, L) :- integer(N), N >= 0, L is 2322000 + 490000 * N.

required_fact(P, income, "household income") :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, "dependents") :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, "exact income") :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    juken_limit(N, L), v_indet(V, L).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(not_target_grade)) :-
    claimant(P), kango_by(C, P), child(C),
    \+ target_grade(C), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, ineligible(income_over)) :-
    claimant(P), kango_by(C, P), child(C),
    val(income(P), V), val(fuyou_ninzu(P), N),
    juken_limit(N, L), v_geq(V, L), !.
kettei_status(P, C, decided(oneoff(200000))) :-
    claimant(P), kango_by(C, P), child(C),
    val(income(P), V), val(fuyou_ninzu(P), N),
    juken_limit(N, L), v_lt(V, L), !.
kettei_status(_, _, error(no_rule_matched)).
