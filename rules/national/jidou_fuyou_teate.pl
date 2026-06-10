% ============================================================
% jidou_fuyou_teate.pl - Child Rearing Allowance (single parent)
% Status: SPIKE v1 (3-valued fact schema, docs/specs/rule-schema.md)
% Semantics verified via prolog-reasoner 2026-06-11:
%   - unknown exclusion -> blocked, never a false decided
%     (regression test for the v0 negation-as-failure bug)
%   - income range straddling a limit -> blocked([income_exact])
%   - confirmed exclusion -> ineligible with statutory reason
% Income limit values are PLACEHOLDERS - VERIFY before use.
% Requires engine.pl (yes/no/unknown/val, v_lt/v_geq/v_indet).
% ============================================================

:- module(jidou_fuyou_teate, [kettei_status/3, required_fact/3]).

:- discontiguous kettei_status/3.
:- discontiguous required_fact/3.

% eligible child: FY-end age <= 18 (structural facts only)
taisho_jido(C) :-
    child(C),
    age_nendo_matsu(C, A),
    A =< 18.

% exclusions fire ONLY on confirmed facts (rule-schema v1 NAF rule)
jogai_confirmed(C, 'child shares livelihood with parent de-facto spouse (Art.4(2) analog)') :-
    yes(seikei_douitsu_partner(C)).

% income limits by number of dependents (PLACEHOLDER base/step VALUES)
% Formula form so EVERY N >= 0 is defined; a table with gaps made
% kettei_status silently unsolvable for N >= 3 (review finding A).
zenbu_limit(N, L)  :- integer(N), N >= 0, L is  690000 + 380000 * N.
ichibu_limit(N, L) :- integer(N), N >= 0, L is 2080000 + 380000 * N.

shikyu_kubun(P, zenbu) :-
    val(income(P), V), val(fuyou_ninzu(P), N),
    zenbu_limit(N, L), v_lt(V, L).
shikyu_kubun(P, ichibu) :-
    val(income(P), V), val(fuyou_ninzu(P), N),
    zenbu_limit(N, L1), v_geq(V, L1),
    ichibu_limit(N, L2), v_lt(V, L2).

% facts required to reach a decision (drives interview agent)
required_fact(P, hitorioya, 'is the household single-parent') :-
    claimant(P), unknown(hitorioya(P)).
required_fact(P, hitorioya_jiyuu, 'statutory single-parent cause (rikon/shibou/...)') :-
    claimant(P), yes(hitorioya(P)), unknown(hitorioya_jiyuu(P)).
required_fact(P, seikei_douitsu_partner, 'does the child live with a de-facto spouse of the parent') :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    unknown(seikei_douitsu_partner(C)).
required_fact(P, income, 'income of claimant (after statutory deduction)') :-
    claimant(P), unknown(income(P)).
required_fact(P, fuyou_ninzu, 'number of tax dependents') :-
    claimant(P), unknown(fuyou_ninzu(P)).
required_fact(P, income_exact, 'exact income (given range straddles a limit)') :-
    claimant(P), val(income(P), V), val(fuyou_ninzu(P), N),
    ( zenbu_limit(N, L), v_indet(V, L)
    ; ichibu_limit(N, L), v_indet(V, L)
    ).

% unified decision protocol, standard clause order (rule-schema v1):
% structural ineligible -> confirmed-no ineligible -> confirmed exclusion
% -> blocked -> decided -> value-based ineligible
kettei_status(P, C, ineligible('child past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    \+ taisho_jido(C), !.                       % NAF over structural facts: safe
kettei_status(P, C, ineligible('no single-parent cause (Art.4(1))')) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    no(hitorioya(P)), !.
kettei_status(P, C, ineligible(Reason)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    jogai_confirmed(C, Reason), !.
kettei_status(P, C, blocked(Missing)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    \+ jogai_confirmed(C, _),
    findall(F, required_fact(P, F, _), Ms),
    sort(Ms, Missing),
    Missing \= [], !.
kettei_status(P, C, decided(Kubun)) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    yes(hitorioya(P)), val(hitorioya_jiyuu(P), _),
    no(seikei_douitsu_partner(C)),
    shikyu_kubun(P, Kubun), !.
kettei_status(P, C, ineligible('income exceeds partial-payment limit')) :-
    claimant(P), kango_by(C, P), taisho_jido(C),
    val(income(P), V), val(fuyou_ninzu(P), N),
    ichibu_limit(N, L), v_geq(V, L), !.
% catch-all: a case no clause covers must surface as an error card,
% never vanish from results (fail-safe; relies on the once() driver)
kettei_status(_, _, error(no_rule_matched)).
