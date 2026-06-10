% ============================================================
% jidou_fuyou_teate.pl - Child Rearing Allowance (single parent)
% Status: SPIKE v1 (3-valued fact schema, docs/specs/rule-schema.md)
% Semantics verified via prolog-reasoner 2026-06-11:
%   - unknown exclusion -> blocked, never a false decided
%     (regression test for the v0 negation-as-failure bug)
%   - income range straddling a limit -> blocked([income_exact])
%   - confirmed exclusion -> ineligible with statutory reason
% Limits and amounts VERIFIED 2026-06-11 (sources fixed in
% tests/golden/jidou_fuyou_teate/statute_source.md).
% Requires engine.pl (yes/no/unknown/val, v_lt/v_geq/v_indet).
% ============================================================

:- module(jidou_fuyou_teate, [kettei_status/3, required_fact/3, teate_amount/2]).

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

% income limits by number of dependents -- VERIFIED against Cabinet Order
% (shikourei Art.2-4, as amended 2024-11): linear, 690,000/2,080,000 base
% + 380,000 per dependent, confirmed for N = 0..5 in the official table.
% Formula form so EVERY N >= 0 is defined; a table with gaps made
% kettei_status silently unsolvable for N >= 3 (review finding A).
zenbu_limit(N, L)  :- integer(N), N >= 0, L is  690000 + 380000 * N.
ichibu_limit(N, L) :- integer(N), N >= 0, L is 2080000 + 380000 * N.

% monthly amounts, FY2026 (Reiwa 8, effective 2026-04) -- VERIFIED
zenbu_base(48050).          % 1st child, full payment
zenbu_kasan(11350).         % 2nd+ child addition, full payment
ichibu_base_start(48040).   % partial: start - (income - full_limit) * coef
ichibu_base_coef(0.0264029).
ichibu_kasan_start(11340).
ichibu_kasan_coef(0.0040719).

shikyu_kubun(P, zenbu) :-
    val(income(P), V), val(fuyou_ninzu(P), N),
    zenbu_limit(N, L), v_lt(V, L).
shikyu_kubun(P, ichibu) :-
    val(income(P), V), val(fuyou_ninzu(P), N),
    zenbu_limit(N, L1), v_geq(V, L1),
    ichibu_limit(N, L2), v_lt(V, L2).

% household monthly amount (per_household unit; aggregation in
% docs/specs/architecture.md). Rounding: nearest 10 yen (official rule).
round10(Raw, Yen) :- Yen is round(Raw / 10) * 10.

% children countable for the amount: per-child eligibility conditions
kasan_count(P, N) :-
    findall(C,
            ( child(C), kango_by(C, P), taisho_jido(C),
              no(seikei_douitsu_partner(C)) ),
            Cs),
    length(Cs, N).

teate_amount(P, Total) :-
    shikyu_kubun(P, zenbu), !,
    kasan_count(P, N), N >= 1,
    zenbu_base(B), zenbu_kasan(K),
    Total is B + K * (N - 1).
teate_amount(P, Total) :-
    shikyu_kubun(P, ichibu), !,
    val(income(P), I), number(I),   % point income required: for ranges the
                                    % runner evaluates both endpoints (spec)
    val(fuyou_ninzu(P), F), zenbu_limit(F, L),
    ichibu_base_start(BS), ichibu_base_coef(BC),
    round10(BS - (I - L) * BC, Base),
    kasan_count(P, N), N >= 1,
    ichibu_kasan_start(KS), ichibu_kasan_coef(KC),
    round10(KS - (I - L) * KC, Kasan),
    Total is Base + Kasan * (N - 1).

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

% unified decision protocol, standard clause order (rule-schema v1.1):
% structural guard -> structural ineligible -> confirmed-no ineligible
% -> confirmed exclusion -> blocked -> decided -> value-based ineligible
% The guard MUST precede the structural ineligible clauses: their bare NAF
% succeeds when structural facts are ABSENT, which would turn "ages
% missing" (a mapping bug) into a wrong "child past FY-end age 18".
kettei_status(P, C, error(structural_facts_missing)) :-
    claimant(P), child(C),
    \+ age_nendo_matsu(C, _), !.
kettei_status(P, C, ineligible('child past FY-end age 18')) :-
    claimant(P), kango_by(C, P), child(C),
    \+ taisho_jido(C), !.                       % NAF over structural facts:
                                                % safe BELOW the guard only
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
