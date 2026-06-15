% ============================================================
% jiritsu_shien_iryo_seishin.pl - Self-reliance Medical Support (Mental)
% VERIFIED 2026-06-15: in-kind (copay reduced to 10%). No income
% limit for eligibility. v1: seishin_1 or seishin_2 as proxy.
% Subject: claimant (self).
% Sources: tests/golden/jiritsu_shien_iryo_seishin/statute_source.md
% Requires engine.pl.
% ============================================================

:- module(jiritsu_shien_iryo_seishin, [kettei_status/3, required_fact/3]).

taisho_seishin(seishin_1).
taisho_seishin(seishin_2).

kettei_status(P, self, ineligible(not_mental_health)) :-
    claimant(P), val(shogai_techo(P), G), \+ taisho_seishin(G), !.
kettei_status(P, self, blocked(Missing)) :-
    claimant(P),
    findall(F, required_fact(P, F, _), Ms), sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, self, decided(in_kind)) :-
    claimant(P), val(shogai_techo(P), G), taisho_seishin(G), !.
kettei_status(_, _, error(no_rule_matched)).

required_fact(P, shogai_techo, "mental health certificate") :-
    claimant(P), unknown(shogai_techo(P)).
