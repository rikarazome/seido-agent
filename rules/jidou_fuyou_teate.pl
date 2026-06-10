% ============================================================
% jidou_fuyou_teate.pl - Child Rearing Allowance (single parent)
% Status: SPIKE (hand-formalized feasibility draft)
% Source: Jidou Fuyou Teate Act. Demonstrates:
%   - statutory exclusion via negation (Art.4(2) analog)
%   - income test with full/partial payment tiers
%   - blocked-status question generation from missing facts
% Income limit values are PLACEHOLDERS - VERIFY before use.
% ============================================================

:- discontiguous kettei_status/3.

% eligible child: FY-end age <= 18 with a single-parent cause
% (one of statutory categories: rikon, shibou, iki, mikon, ...)
taisho_jido(C) :-
    child(C),
    age_nendo_matsu(C, A),
    A =< 18,
    hitorioya_jiyuu(C, _).

% exclusions, each with the violated provision as reason
jogai(C, 'child shares livelihood with parent de-facto spouse (Art.4(2) analog)') :-
    seikei_douitsu_partner(C).

jifu_eligible(P, C) :-
    claimant(P),
    kango_by(C, P),
    taisho_jido(C),
    \+ jogai(C, _).

% income limits by number of dependents (PLACEHOLDER VALUES)
zenbu_limit(0, 690000).
zenbu_limit(1, 1070000).
zenbu_limit(2, 1450000).
ichibu_limit(0, 2080000).
ichibu_limit(1, 2460000).
ichibu_limit(2, 2840000).

shikyu_kubun(P, zenbu) :-
    income(P, I), fuyou_ninzu(P, N), zenbu_limit(N, L), I < L.
shikyu_kubun(P, ichibu) :-
    income(P, I), fuyou_ninzu(P, N),
    zenbu_limit(N, L1), I >= L1,
    ichibu_limit(N, L2), I < L2.
shikyu_kubun(P, fushikyu) :-
    income(P, I), fuyou_ninzu(P, N), ichibu_limit(N, L2), I >= L2.

% facts required to reach a decision (drives interview agent)
required_fact(P, income, 'annual income of claimant') :-
    claimant(P), \+ income(P, _).
required_fact(P, fuyou_ninzu, 'number of tax dependents') :-
    claimant(P), \+ fuyou_ninzu(P, _).

% unified decision protocol: decided / blocked / ineligible
kettei_status(P, C, decided(Kubun)) :-
    jifu_eligible(P, C),
    shikyu_kubun(P, Kubun).
kettei_status(P, C, blocked(Missing)) :-
    jifu_eligible(P, C),
    \+ shikyu_kubun(P, _),
    findall(F, required_fact(P, F, _), Missing),
    Missing \= [].
kettei_status(P, C, ineligible(Reason)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    jogai(C, Reason).
