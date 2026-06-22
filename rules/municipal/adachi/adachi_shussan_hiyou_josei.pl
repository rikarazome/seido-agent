% adachi_shussan_hiyou_josei.pl - Adachi ward childbirth expense subsidy
% VERIFIED 2026-06-22: Up to 100,000 JPY per child (self-pay portion).
% Requires: pregnancy/birth, Adachi resident 1+ years, not on seikatsu_hogo.
% Source: https://www.city.adachi.tokyo.jp/oyako/k-kyoiku/kosodate/syussanhi-josei.html

:- module(adachi_shussan_hiyou_josei, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy/birth") :-
    claimant(P), unknown(ninshin(P)).
required_fact(P, seikatsu_hogo, "seikatsu hogo status") :-
    claimant(P), unknown(seikatsu_hogo(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, ineligible(receiving_seikatsu_hogo)) :-
    claimant(P), val(seikatsu_hogo(P), true), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, decided(kubun(adachi_shussan_hiyou))) :-
    claimant(P), yes(ninshin(P)), no(seikatsu_hogo(P)), !.
kettei_status(_, _, error(no_rule_matched)).
