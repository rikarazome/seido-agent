% setagaya_shussan_hiyou_josei.pl - Setagaya ward childbirth expense subsidy
% VERIFIED 2026-06-22: 50,000 JPY per child (fixed amount).
% Source: https://www.city.setagaya.lg.jp/02413/1206.html

:- module(setagaya_shussan_hiyou_josei, [kettei_status/3, required_fact/3]).

required_fact(P, ninshin, "pregnancy/birth") :-
    claimant(P), unknown(ninshin(P)).

kettei_status(P, self, ineligible(not_pregnant)) :-
    claimant(P), no(ninshin(P)), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, decided(oneoff(50000))) :-
    claimant(P), yes(ninshin(P)), !.
kettei_status(_, _, error(no_rule_matched)).
