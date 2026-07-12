:- module(self_medication, [kettei_status/3, required_fact/3]).

% NTA Tax Answer No.1129 (statute_source.md, snapshot 2026-06-21): the
% credit requires BOTH switch-OTC purchases over 12,000 yen/year AND a
% health-maintenance action (checkup, vaccination etc.), and is an
% alternative to the regular medical-expense deduction. Questions cascade:
% OTC is only asked once the regular deduction is ruled out, the checkup
% question only once the OTC threshold is met.
required_fact(P, iryouhi_10man, "medical expenses check") :-
    claimant(P), unknown(iryouhi_10man(P)).
required_fact(P, otc_12000, "switch-OTC purchases over 12000 yen") :-
    claimant(P), val(iryouhi_10man(P), false), unknown(otc_12000(P)).
required_fact(P, kenshin_torikumi, "health checkup etc. requirement") :-
    claimant(P), val(iryouhi_10man(P), false), val(otc_12000(P), true),
    unknown(kenshin_torikumi(P)).

kettei_status(P, self, ineligible(iryouhi_koujo_available)) :-
    claimant(P), val(iryouhi_10man(P), true), !.
kettei_status(P, self, ineligible(otc_not_over_12000)) :-
    claimant(P), val(otc_12000(P), false), !.
kettei_status(P, self, ineligible(no_kenshin_torikumi)) :-
    claimant(P), val(kenshin_torikumi(P), false), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P), findall(F, required_fact(P, F, _), Fs), sort(Fs, Missing), Missing \= [], !.
kettei_status(P, self, decided(kubun(self_medication))) :-
    claimant(P), val(iryouhi_10man(P), false), val(otc_12000(P), true),
    val(kenshin_torikumi(P), true), !.
kettei_status(_, _, error(no_rule_matched)).
