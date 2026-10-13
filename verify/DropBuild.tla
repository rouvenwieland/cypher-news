---- MODULE DropBuild ----
(* Models scheduler.run_due / run_for_user: several concurrent run_due executions
   (scheduler loop, keep-awake kick via /healthz, POST /api/cron) and an account deletion.
   FIXED = FALSE: code as on design-overhaul-2026-10 (before the fix).
   FIXED = TRUE : with the per-user in-flight guard, the already_done recheck and the "user still exists" check at insert time.
   One calendar day (last_drop_day == today is the boolean lastDone). *)
EXTENDS Naturals, FiniteSets

CONSTANTS Users, Workers, FIXED

VARIABLES lastDone, inflight, drops, alive, pc, todo, cur

vars == <<lastDone, inflight, drops, alive, pc, todo, cur>>

Init == /\ lastDone = [u \in Users |-> FALSE]
        /\ inflight = {}
        /\ drops = [u \in Users |-> 0]
        /\ alive = [u \in Users |-> TRUE]
        /\ pc = [w \in Workers |-> "idle"]
        /\ todo = [w \in Workers |-> {}]
        /\ cur = [w \in Workers |-> CHOOSE u \in Users : TRUE]

\* due_users(): snapshot of everybody not yet delivered today
Scan(w) == /\ pc[w] = "idle"
           /\ todo' = [todo EXCEPT ![w] = {u \in Users : ~lastDone[u] /\ alive[u]}]
           /\ pc' = [pc EXCEPT ![w] = "pick"]
           /\ UNCHANGED <<lastDone, inflight, drops, alive, cur>>

Pick(w) == /\ pc[w] = "pick"
           /\ IF todo[w] = {}
                 THEN /\ pc' = [pc EXCEPT ![w] = "done"]
                      /\ UNCHANGED <<todo, cur>>
                 ELSE \E u \in todo[w] :
                         /\ cur' = [cur EXCEPT ![w] = u]
                         /\ todo' = [todo EXCEPT ![w] = @ \ {u}]
                         /\ pc' = [pc EXCEPT ![w] = "start"]
           /\ UNCHANGED <<lastDone, inflight, drops, alive>>

\* start of run_for_user: read the user row
Start(w) == /\ pc[w] = "start"
            /\ LET u == cur[w] IN
               IF ~alive[u]
                  THEN /\ pc' = [pc EXCEPT ![w] = "pick"] /\ UNCHANGED inflight
                  ELSE IF FIXED
                       THEN IF u \in inflight \/ lastDone[u]
                               THEN /\ pc' = [pc EXCEPT ![w] = "pick"] /\ UNCHANGED inflight
                               ELSE /\ inflight' = inflight \cup {u} /\ pc' = [pc EXCEPT ![w] = "build"]
                       ELSE /\ pc' = [pc EXCEPT ![w] = "build"] /\ UNCHANGED inflight
            /\ UNCHANGED <<lastDone, drops, alive, todo, cur>>

Build(w) == /\ pc[w] = "build"
            /\ pc' = [pc EXCEPT ![w] = "commit"]
            /\ UNCHANGED <<lastDone, inflight, drops, alive, todo, cur>>

Commit(w) == /\ pc[w] = "commit"
             /\ LET u == cur[w] IN
                IF FIXED /\ ~alive[u]
                   THEN UNCHANGED <<drops, lastDone>>
                   ELSE /\ drops' = [drops EXCEPT ![u] = @ + 1]
                        /\ lastDone' = [lastDone EXCEPT ![u] = TRUE]
             /\ inflight' = inflight \ {cur[w]}
             /\ pc' = [pc EXCEPT ![w] = "pick"]
             /\ UNCHANGED <<alive, todo, cur>>

\* DELETE /api/me: removes the user and all of his drops
Delete(u) == /\ alive[u]
             /\ alive' = [alive EXCEPT ![u] = FALSE]
             /\ drops' = [drops EXCEPT ![u] = 0]
             /\ UNCHANGED <<lastDone, inflight, pc, todo, cur>>

Next == (\E w \in Workers : Scan(w) \/ Pick(w) \/ Start(w) \/ Build(w) \/ Commit(w))
        \/ (\E u \in Users : Delete(u))

Spec == Init /\ [][Next]_vars

OnePerDay == \A u \in Users : drops[u] <= 1
NoOrphan  == \A u \in Users : alive[u] \/ drops[u] = 0
TypeOK    == /\ drops \in [Users -> 0..Cardinality(Workers)]
====
