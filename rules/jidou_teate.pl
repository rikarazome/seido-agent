% ============================================================
% jidou_teate.pl - Child Allowance (Jidou Teate Act, post 2024-10 reform)
% Status: SPIKE v1 (module form, docs/specs/rule-schema.md)
% Source: Jidou Teate Act as amended 2024-10 (no income limit,
%         covers children up to end of FY of 18th birthday,
%         3rd+ child 30,000 JPY, multi-child counting up to
%         end of FY of 22nd birthday)
% Amounts/boundaries: TO BE VERIFIED against official text.
% This program uses STRUCTURAL facts only (ages, custody), which
% the mapping layer always supplies, so bare negation is safe here.
% Requires engine.pl.
% ============================================================

:- module(jidou_teate, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

% eligible child: until first March 31 after 18th birthday
shikyu_taisho_jido(C) :-
    child(C),
    age_nendo_matsu(C, A),
    A =< 18.

% multi-child counting: children up to FY-end age 22,
% cared for and financially supported by claimant
tashi_count(P, C) :-
    child(C),
    kango_by(C, P),
    seikei_futan(P, C),
    age_nendo_matsu(C, A),
    A =< 22.

% rank among counted children (eldest = 1)
child_rank(P, C, Rank) :-
    tashi_count(P, C),
    age_nendo_matsu(C, AC),
    findall(D, (tashi_count(P, D), age_nendo_matsu(D, AD), AD > AC), Ds),
    length(Ds, N),
    Rank is N + 1.

% monthly amount (no income test since 2024-10)
jidou_teate_getsugaku(P, C, 30000) :-
    shikyu_taisho_jido(C), kango_by(C, P),
    child_rank(P, C, R), R >= 3.
jidou_teate_getsugaku(P, C, 15000) :-
    shikyu_taisho_jido(C), kango_by(C, P),
    child_rank(P, C, R), R < 3,
    age(C, A), A < 3.
jidou_teate_getsugaku(P, C, 10000) :-
    shikyu_taisho_jido(C), kango_by(C, P),
    child_rank(P, C, R), R < 3,
    age(C, A), A >= 3.

% household total per month
jidou_teate_total(P, Total) :-
    claimant(P),
    findall(Y, jidou_teate_getsugaku(P, _, Y), Ys),
    Ys \= [],
    sum_list(Ys, Total).

% guard: ages are structural and guaranteed by the mapping layer,
% but keep the check so a mapping bug surfaces as blocked, not silence
required_fact(P, child_ages, 'ages of all children') :-
    claimant(P), \+ age_nendo_matsu(_, _).

% unified decision protocol
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), child(C),
    findall(F, required_fact(P, F, _), Ms),
    sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, ineligible('child past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    \+ shikyu_taisho_jido(C), !.
kettei_status(P, C, decided(amount(Y))) :-
    jidou_teate_getsugaku(P, C, Y), !.
% catch-all: a case no clause covers must surface as an error card,
% never vanish from results (fail-safe; relies on the once() driver)
kettei_status(_, _, error(no_rule_matched)).
