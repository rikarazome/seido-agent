% ============================================================
% nanbyo_iryo_josei.pl - Intractable Disease Medical Subsidy
% VERIFIED 2026-06-15: in-kind medical cost reduction for certified
% intractable disease patients. No income limit for eligibility
% (income affects copay ceiling only). Subject: claimant (self).
% Sources: tests/golden/nanbyo_iryo_josei/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(nanbyo_iryo_josei, [kettei_status/3, required_fact/3]).

kettei_status(P, self, ineligible(not_certified)) :-
    claimant(P), no(nanbyo_nintei(P)), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, decided(in_kind)) :-
    claimant(P), yes(nanbyo_nintei(P)), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, nanbyo_nintei, "intractable disease certification") :-
    claimant(P), unknown(nanbyo_nintei(P)).
