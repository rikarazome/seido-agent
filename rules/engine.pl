% ============================================================
% engine.pl - shared inference helpers (rule-schema v1)
% Loaded into `user` (NOT a module) so that every program module
% inherits these predicates and the dynamic known/2 store.
% Semantics verified via prolog-reasoner 2026-06-11.
%
% The proof-tree meta-interpreter (ported from prolog-reasoner)
% is added here in Week 2 integration; see docs/roadmap.md.
% ============================================================

:- dynamic known/2.

% ----- 3-valued access to askable facts -----
% unknown = no known/2 clause. Rules must NEVER apply bare \+ to
% askable facts; use no/1 (confirmed false) instead.
yes(F)     :- known(F, true).
no(F)      :- known(F, false).
unknown(F) :- \+ known(F, _).
val(F, V)  :- known(F, V).

% ----- interval-aware comparison -----
% Values are numbers or range(Lo, Hi) from form range inputs.
% Comparisons succeed only when the WHOLE range satisfies them.
v_lt(V, L)  :- number(V), V < L.
v_lt(range(_, Hi), L)  :- number(Hi), Hi < L.
v_geq(V, L) :- number(V), V >= L.
v_geq(range(Lo, _), L) :- number(Lo), Lo >= L.
% type guard: without it a garbage value (atom, inverted range) fails
% both comparisons and fake-succeeds as "indeterminate", turning a type
% bug into a silent extra question instead of an error
valid_val(V) :- number(V).
valid_val(range(Lo, Hi)) :- number(Lo), number(Hi), Lo =< Hi.
% range straddles the threshold -> neither holds -> ask exact value
v_indet(V, L) :- valid_val(V), \+ v_lt(V, L), \+ v_geq(V, L).

% ----- proof-tree meta-interpreter (stage 2 of two-stage re-derivation) ---
% Usage: fix the GROUND status with a plain once() query first, then call
% prove(Module, kettei_status(P, C, Status), Proof) on that ground term.
% Cut is treated as true, which is sound ONLY for ground re-derivation
% (other clauses' heads cannot unify with a different ground status --
% verified, see docs/specs/rule-schema.md). Direct-vs-meta agreement is
% asserted on every golden case in CI.
% Supported body constructs: conjunction, disjunction, negation, cut,
% built-ins (leaf), user clauses. If a rule ever uses if-then-else the
% agreement test will catch the gap.
prove(_, true, true) :- !.
prove(M, (A, B), and(PA, PB)) :- !,
    prove(M, A, PA), prove(M, B, PB).
prove(M, (A ; B), or(P)) :- !,
    ( prove(M, A, P) ; prove(M, B, P) ).
prove(_, !, cut) :- !.
% negation-as-failure appears in the proof as an explicit leaf: this is
% how "no exclusion applies" becomes visible in the explanation
prove(M, \+ A, naf(A)) :- !,
    \+ prove(M, A, _).
prove(M, Goal, builtin(Goal)) :-
    catch(predicate_property(M:Goal, built_in), _, fail), !,
    call(M:Goal).
prove(M, Goal, node(Goal, Sub)) :-
    prove_clause(M, Goal, Body),
    prove(M, Body, Sub).

% clause lookup: module first (covers module-local and, via SWI's default
% module chain, user-inherited predicates); explicit user fallback for
% interpreters where M:G does not resolve inherited definitions
prove_clause(M, G, B) :- catch(clause(M:G, B), _, fail).
prove_clause(M, G, B) :- M \== user, catch(clause(user:G, B), _, fail).
