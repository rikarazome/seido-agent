% ============================================================
% shussan_kosodate_ouen.pl - Childbirth/Childcare Support Grant
% VERIFIED 2026-06-15: 100,000 JPY total (50,000 pregnancy +
% 50,000 birth). No income limit. Requires pregnancy.
% v1 simplification: shows full 100,000 if currently pregnant.
% Sources: tests/golden/shussan_kosodate_ouen/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(shussan_kosodate_ouen, [kettei_status/3, required_fact/3]).

kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, decided(amount(100000))) :-
    claimant(P), yes(ninshin(P)), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, ninshin, "pregnancy status") :-
    claimant(P), unknown(ninshin(P)).
