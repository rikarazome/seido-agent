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
v_lt(range(_, Hi), L)  :- Hi < L.
v_geq(V, L) :- number(V), V >= L.
v_geq(range(Lo, _), L) :- Lo >= L.
% range straddles the threshold -> neither holds -> ask exact value
v_indet(V, L) :- \+ v_lt(V, L), \+ v_geq(V, L).
