% ============================================================
% jidou_teate.pl - Child Allowance (Jidou Teate Act, post 2024-10 reform)
% Status: SPIKE (hand-formalized feasibility draft)
% Source: Jidou Teate Act as amended 2024-10 (no income limit,
%         covers children up to end of FY of 18th birthday,
%         3rd+ child 30,000 JPY, multi-child counting up to
%         end of FY of 22nd birthday)
% Amounts/boundaries: TO BE VERIFIED against official text.
% ============================================================

:- discontiguous kettei_status/3.

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

% required facts for question generation
required_fact_jt(P, child_ages, 'ages of all children') :-
    claimant(P), \+ age_nendo_matsu(_, _).

% unified decision protocol
kettei_status(P, C, decided(amount(Y))) :-
    jidou_teate_getsugaku(P, C, Y).
