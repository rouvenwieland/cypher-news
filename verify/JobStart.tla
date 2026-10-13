---- MODULE JobStart ----
(* Models app.make_drop (POST /api/drop with X-Client: 2): "is a job already running?" check, rate limit, then registering
   the new job and starting its thread. In the code before the fix the check and the registration were two SEPARATE lock
   sections, with the rate limiter in between. ATOMIC = TRUE is the fixed version (one lock section). *)
EXTENDS Naturals, FiniteSets

CONSTANTS Requests, ATOMIC

VARIABLES job, threads, pc

vars == <<job, threads, pc>>

Init == /\ job = "none"          \* _jobs[uid].state: none | running | done
        /\ threads = 0           \* live background threads building a drop for this user
        /\ pc = [r \in Requests |-> "new"]

\* ORIGINAL: step 1 = check under lock, step 2 = rate limit (no lock), step 3 = register under lock + start thread
Check(r) == /\ ~ATOMIC /\ pc[r] = "new"
            /\ IF job = "running" THEN pc' = [pc EXCEPT ![r] = "end"] ELSE pc' = [pc EXCEPT ![r] = "checked"]
            /\ UNCHANGED <<job, threads>>

Register(r) == /\ ~ATOMIC /\ pc[r] = "checked"
               /\ job' = "running" /\ threads' = threads + 1
               /\ pc' = [pc EXCEPT ![r] = "end"]

\* FIXED: check, rate limit and registration inside one lock section
AtomicStart(r) == /\ ATOMIC /\ pc[r] = "new"
                  /\ IF job = "running" THEN /\ pc' = [pc EXCEPT ![r] = "end"] /\ UNCHANGED <<job, threads>>
                     ELSE /\ job' = "running" /\ threads' = threads + 1 /\ pc' = [pc EXCEPT ![r] = "end"]

Finish == /\ threads > 0
          /\ threads' = threads - 1
          /\ job' = IF threads = 1 THEN "done" ELSE job
          /\ UNCHANGED pc

Next == (\E r \in Requests : Check(r) \/ Register(r) \/ AtomicStart(r)) \/ Finish

Spec == Init /\ [][Next]_vars

AtMostOneBuild == threads <= 1
====
