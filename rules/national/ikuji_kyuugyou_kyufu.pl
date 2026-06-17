% ikuji_kyuugyou_kyufu - Childcare Leave Benefit
% 雇用保険法61条の7. koyou_hoken + ikuji_kyuugyou.
:- module(ikuji_kyuugyou_kyufu, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, ikuji_kyuugyou, "childcare leave status") :-
    claimant(P), val(koyou_hoken(P), true), unknown(ikuji_kyuugyou(P)).

kettei_status(P, self, ineligible(no_koyou_hoken)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(not_on_leave)) :-
    claimant(P), val(ikuji_kyuugyou(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(ikuji_kyuugyou))) :-
    claimant(P), val(koyou_hoken(P), true), val(ikuji_kyuugyou(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
