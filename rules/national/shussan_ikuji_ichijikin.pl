% ============================================================
% shussan_ikuji_ichijikin.pl - Lump-sum Birth Allowance
% VERIFIED 2026-06-15: 500,000 JPY per birth (assuming enrollment
% in the Obstetric Compensation System; 488,000 JPY otherwise,
% but this version uses 500,000 fixed).
% Conditions: health insurance enrollment + pregnancy/birth.
% No income limit. Subject: claimant (self).
% Sources: tests/golden/shussan_ikuji_ichijikin/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(shussan_ikuji_ichijikin, [kettei_status/3, required_fact/3]).

kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, ineligible(no_health_insurance)) :-
    claimant(P), yes(ninshin(P)), no(kenkou_hoken(P)), !.
kettei_status(P, self, decided(amount(500000))) :-
    claimant(P), yes(ninshin(P)), yes(kenkou_hoken(P)), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).
required_fact(P, kenkou_hoken, "health insurance") :-
    claimant(P), unknown(kenkou_hoken(P)).
