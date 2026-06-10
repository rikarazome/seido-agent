% ============================================================
% tokyo_018_support.pl - Tokyo 018 Support (child benefit, no income test)
% VERIFIED 2026-06-11: 5,000 JPY/month per child, age 0 to FY-end of 18,
% no income limit (sources in tests/golden/tokyo_018_support/
% statute_source.md). Tokyo residence is implied by the form's
% municipality selection (this module is only loaded for Tokyo wards).
% Requires engine.pl.
% ============================================================

:- module(tokyo_018_support, [kettei_status/3, required_fact/3]).

% no askable facts: age and residence are structural
required_fact(_, _, _) :- fail.

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A > 18, !.
kettei_status(P, C, decided(monthly(5000))) :-
    claimant(P), kango_by(C, P), child(C), !.
kettei_status(_, _, error(no_rule_matched)).
