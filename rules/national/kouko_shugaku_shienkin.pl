% ============================================================
% kouko_shugaku_shienkin.pl - High School Tuition Support Fund
% Income test ABOLISHED 2026-04 (Act amendment passed 2026-03-31).
% Amounts VERIFIED 2026-06-11: public 118,800 JPY/yr, private up to
% 457,200 JPY/yr (sources in tests/golden/kouko_shugaku_shienkin/
% statute_source.md). v1 scope: full-time public/private only; the
% 36-month cap, graduation and nationality requirements are shown as
% notes on the result card, not asked.
% Uses PER-CHILD askables: koukou_zaigaku, gakkou_kubun.
% Requires engine.pl.
% ============================================================

:- module(kouko_shugaku_shienkin, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

% high-school age band: FY-end age 16..18
koukousei_nendai(C) :-
    child(C), age_nendo_matsu(C, A), A >= 16, A =< 18.

required_fact(P, koukou_zaigaku, 'is the child enrolled in a high school etc.') :-
    claimant(P), kango_by(C, P), koukousei_nendai(C),
    unknown(koukou_zaigaku(C)).
required_fact(P, gakkou_kubun, 'school type (public / private full-time)') :-
    claimant(P), kango_by(C, P), koukousei_nendai(C),
    yes(koukou_zaigaku(C)), unknown(gakkou_kubun(C)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('not high-school age (FY-end 16-18)')) :-
    claimant(P), kango_by(C, P), child(C),
    \+ koukousei_nendai(C), !.
kettei_status(P, C, ineligible('not enrolled in an eligible high school')) :-
    claimant(P), kango_by(C, P),
    no(koukou_zaigaku(C)), !.
kettei_status(P, C, blocked([koukou_zaigaku])) :-
    claimant(P), kango_by(C, P),
    unknown(koukou_zaigaku(C)), !.
kettei_status(P, C, blocked([gakkou_kubun])) :-
    claimant(P), kango_by(C, P),
    yes(koukou_zaigaku(C)), unknown(gakkou_kubun(C)), !.
kettei_status(P, C, decided(amount_yearly(118800))) :-
    claimant(P), kango_by(C, P),
    yes(koukou_zaigaku(C)), val(gakkou_kubun(C), kouritsu), !.
kettei_status(P, C, decided(amount_yearly_max(457200))) :-
    claimant(P), kango_by(C, P),
    yes(koukou_zaigaku(C)), val(gakkou_kubun(C), shiritsu), !.
kettei_status(_, _, error(no_rule_matched)).
