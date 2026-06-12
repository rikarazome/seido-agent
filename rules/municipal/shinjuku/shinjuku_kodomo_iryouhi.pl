% ============================================================
% shinjuku_kodomo_iryouhi.pl - shinjuku ward child medical cost subsidy
% VERIFIED 2026-06-12: in-kind benefit (insured co-payment covered),
% age 0 to FY-end of 18, public health insurance required, no income
% test. Generated from the shibuya template by
% scripts/gen_ward_iryouhi.py -- do not edit by hand; source fixation
% in tests/golden/shinjuku_kodomo_iryouhi/statute_source.md.
% Ward residence is implied by the form's municipality selection.
% Requires engine.pl.
% ============================================================

:- module(shinjuku_kodomo_iryouhi, [kettei_status/3, required_fact/3]).

required_fact(P, kenkou_hoken, 'is the household covered by public health insurance') :-
    claimant(P), unknown(kenkou_hoken(P)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A > 18, !.
kettei_status(P, C, ineligible('not covered by public health insurance')) :-
    claimant(P), kango_by(C, P),
    no(kenkou_hoken(P)), !.
kettei_status(P, C, blocked([kenkou_hoken])) :-
    claimant(P), kango_by(C, P),
    unknown(kenkou_hoken(P)), !.
kettei_status(P, C, decided(in_kind(jiko_futan_josei))) :-
    claimant(P), kango_by(C, P),
    yes(kenkou_hoken(P)), !.
kettei_status(_, _, error(no_rule_matched)).
