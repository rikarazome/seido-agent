% tokutei_shishutsu_koujo - Specified Expense Deduction
% Income Tax Act Art.57-2. koyou_hoken + tokutei_shishutsu_ari.
:- module(tokutei_shishutsu_koujo, [kettei_status/3, required_fact/3]).

required_fact(P, koyou_hoken, "koyou hoken enrollment") :-
    claimant(P), unknown(koyou_hoken(P)).
required_fact(P, tokutei_shishutsu_ari, "specified expense exceeds threshold") :-
    claimant(P), val(koyou_hoken(P), true), unknown(tokutei_shishutsu_ari(P)).

kettei_status(P, self, ineligible(not_salaryman)) :-
    claimant(P), val(koyou_hoken(P), false), !.
kettei_status(P, self, ineligible(no_tokutei_shishutsu)) :-
    claimant(P), val(tokutei_shishutsu_ari(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(tokutei_shishutsu))) :-
    claimant(P), val(koyou_hoken(P), true), val(tokutei_shishutsu_ari(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
