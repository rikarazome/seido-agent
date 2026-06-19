% adachi_ninkagai_hoiku_hojo.pl - adachi ward unlicensed daycare subsidy
% Source: city.adachi.tokyo.jp/kodomo-nyuuen/ninnkagai_teikiriyou.html
% 0-2 taxed: 80,000/mo, 0-2 non-taxed: 80,000/mo, 3-5: 77,000/mo
% Subject: child. FY-end age 0-5.

:- module(adachi_ninkagai_hoiku_hojo, [kettei_status/3, required_fact/3]).

required_fact(P, hikazei, "non-taxable household") :-
    claimant(P), unknown(hikazei(P)).

kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C), \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible(not_target_age)) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A > 5, !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), child(C),
    findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, C, decided(monthly(80000))) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A =< 2, !.
kettei_status(P, C, decided(monthly(77000))) :-
    claimant(P), kango_by(C, P), child(C),
    age_nendo_matsu(C, A), A >= 3, A =< 5, !.
kettei_status(_, _, error(no_rule_matched)).
