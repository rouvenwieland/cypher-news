---- MODULE BackupRestore ----
(* Models cypher/backup.py: the SQLite file lives on an ephemeral disk, the only durable copy is the private HF dataset
   (variable remote). An instance boots with restore_or_die(), then writes, and uploads snapshots every 5 minutes.
   Version numbers stand for "how much user data the DB contains".
   MISCLASS = TRUE : restore() mistakes an existing-but-unreadable backup for "nothing there yet" (RepositoryNotFoundError
                     is also what HF raises for auth problems) and starts with a fresh DB.
   Instances        : more than one means two instances overlap (e.g. a deploy while the old one still runs). *)
EXTENDS Integers

CONSTANTS Instances, MISCLASS, MaxV

VARIABLES remote, local, up   \* remote: version or -1 (no file); local[i]: version or -1 (no file); up[i]: instance serving

vars == <<remote, local, up>>

Init == /\ remote = -1
        /\ local = [i \in Instances |-> -1]
        /\ up = [i \in Instances |-> FALSE]

\* container restart: ephemeral disk is gone
Crash(i) == /\ up[i]
            /\ local' = [local EXCEPT ![i] = -1] /\ up' = [up EXCEPT ![i] = FALSE] /\ UNCHANGED remote

\* restore_or_die(): copy remote if there is no local file; otherwise "fresh"
BootOk(i) == /\ ~up[i]
             /\ IF local[i] # -1 THEN local' = local
                ELSE IF remote = -1 THEN local' = [local EXCEPT ![i] = 0]
                ELSE local' = [local EXCEPT ![i] = remote]
             /\ up' = [up EXCEPT ![i] = TRUE] /\ UNCHANGED remote

\* the misclassification: backup exists, treated as absent
BootMisclass(i) == /\ MISCLASS /\ ~up[i] /\ local[i] = -1 /\ remote # -1
                   /\ local' = [local EXCEPT ![i] = 0] /\ up' = [up EXCEPT ![i] = TRUE] /\ UNCHANGED remote

\* a restore error (corrupt, network): the app refuses to start; modelled by simply not booting (no action needed)

Write(i) == /\ up[i] /\ local[i] < MaxV
            /\ local' = [local EXCEPT ![i] = @ + 1] /\ UNCHANGED <<remote, up>>

Upload(i) == /\ up[i] /\ remote' = local[i] /\ UNCHANGED <<local, up>>

Next == \E i \in Instances : Crash(i) \/ BootOk(i) \/ BootMisclass(i) \/ Write(i) \/ Upload(i)

Spec == Init /\ [][Next]_vars

\* the durable copy must never get older / emptier
RemoteNeverRegresses == [][remote' >= remote]_vars
====
