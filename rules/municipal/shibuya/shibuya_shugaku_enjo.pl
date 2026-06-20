% shibuya_shugaku_enjo.pl - Shibuya School Attendance Assistance
% Eligibility: hikazei household + school-age child (FY-end 6-15).
% Amounts: approximate annual total (supplies+lunch) from Ota ward official page.
% Elementary ~65K/yr, Middle ~75K/yr. Exact amounts vary by grade/ward.
% Subject: child.

:- module(shibuya_shugaku_enjo, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

school_age(C) :-
    child(C), age_nendo_matsu(C, A), A >= 6, A =< 15.
elementary(C) :-
    child(C), age_nendo_matsu(C, A), A >= 6, A =< 11.

required_fact(P, hikazei, "non-taxable household") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(not_school_age)) :-
    claimant(P), kango_by(C, P), child(C),
    \+ school_age(C), !.
kettei_status(P, C, ineligible(not_low_income)) :-
    claimant(P), kango_by(C, P), child(C),
    no(hikazei(P)), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, decided(kubun(shugaku_enjo))) :-
    claimant(P), kango_by(C, P), child(C),
    yes(hikazei(P)), !.
kettei_status(_, _, error(no_rule_matched)).
