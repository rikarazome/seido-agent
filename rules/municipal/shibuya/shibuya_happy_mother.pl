% shibuya_happy_mother.pl - Shibuya ward Happy Mother childbirth subsidy
% VERIFIED 2026-06-22: Up to 100,000 JPY per birth.
% Source: https://www.city.shibuya.tokyo.jp/kodomo/ninshin/ninshin-teate/happy_josei.html

:- module(shibuya_happy_mother, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy/birth") :-
    claimant(P), unknown(ninshin(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, decided(kubun(shibuya_happy_mother))) :-
    claimant(P), yes(ninshin(P)), !.
kettei_status(_, _, error(no_rule_matched)).
