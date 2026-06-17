% shuugyou_sokushin_teate - Employment Promotion Settlement Allowance
% 雇用保険法56条の3第3項. Requires sai_shushoku_teate received.
:- module(shuugyou_sokushin_teate, [kettei_status/3, required_fact/3]).

required_fact(P, sai_shushoku_teate_jukyuu, "sai shushoku teate received") :-
    claimant(P), unknown(sai_shushoku_teate_jukyuu(P)).

kettei_status(P, self, ineligible(no_sai_shushoku)) :-
    claimant(P), val(sai_shushoku_teate_jukyuu(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(teichaku_teate))) :-
    claimant(P), val(sai_shushoku_teate_jukyuu(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
