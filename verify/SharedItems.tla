---- MODULE SharedItems ----
(* Lifecycle of items shared into the app (table shared, column used). Invariant: an item is only consumed (used=1)
   if it was part of a drop that was really delivered. BUILD_MARKS_EARLY = TRUE is the code before the fix (collect()
   set used=1 for ALL unused rows before the AI call); FALSE = marked after a successful build, only the fetched rows. *)
EXTENDS Naturals, FiniteSets

CONSTANTS Items, Limit, BUILD_MARKS_EARLY

VARIABLES used, delivered, fetched, phase

vars == <<used, delivered, fetched, phase>>

Init == /\ used = {} /\ delivered = {} /\ fetched = {} /\ phase = "idle"

\* collect(): SELECT ... LIMIT 10 over unused rows
Collect == /\ phase = "idle"
           /\ \E f \in SUBSET (Items \ used) :
                 /\ Cardinality(f) <= Limit
                 /\ f # {} \/ (Items \ used) = {}
                 /\ (Cardinality(f) = Limit \/ f = Items \ used)
                 /\ fetched' = f
                 /\ used' = IF BUILD_MARKS_EARLY THEN used \cup (Items \ used) ELSE used
           /\ phase' = "building"
           /\ UNCHANGED delivered

\* AI call succeeds: the drop is delivered
BuildOk == /\ phase = "building"
           /\ delivered' = delivered \cup fetched
           /\ used' = IF BUILD_MARKS_EARLY THEN used ELSE used \cup fetched
           /\ phase' = "idle"
           /\ UNCHANGED fetched

\* AI call fails (rate limit, no credit): nothing delivered
BuildFails == /\ phase = "building"
              /\ phase' = "idle"
              /\ UNCHANGED <<used, delivered, fetched>>

Next == Collect \/ BuildOk \/ BuildFails

Spec == Init /\ [][Next]_vars

NoLoss == used \subseteq delivered \/ phase = "building"
====
