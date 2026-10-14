---- MODULE DropRestart ----
(* Round 2 (2026-10-14): restart of the (now always awake) Render service in the middle of a scheduled drop.
   Render has no persistent disk: on boot the DB is restored from the last backup upload (every 5 min before the fix).
   One user, one day, one scheduler (overlapping runs are covered by DropBuild.tla).
   FIXED = FALSE: drop saved -> push sent at once; upload only on the next tick.
   FIXED = TRUE : drop saved -> backup.nudge(); the push waits until the backup contains the drop (scheduler._notify). *)
EXTENDS Naturals

CONSTANTS FIXED, MaxRestarts

VARIABLES localDone, localDrops, remoteDone, remoteDrops, pc, pushes, builds, restarts

vars == <<localDone, localDrops, remoteDone, remoteDrops, pc, pushes, builds, restarts>>

Init == /\ localDone = FALSE /\ localDrops = 0
        /\ remoteDone = FALSE /\ remoteDrops = 0
        /\ pc = "idle" /\ pushes = 0 /\ builds = 0 /\ restarts = 0

\* due_users() + run_for_user(): not delivered today -> build (AI calls on the user's key)
StartBuild == /\ pc = "idle" /\ ~localDone
              /\ pc' = "building" /\ builds' = builds + 1
              /\ UNCHANGED <<localDone, localDrops, remoteDone, remoteDrops, pushes, restarts>>

\* INSERT INTO drops + last_drop_day = today (one transaction)
Save == /\ pc = "building"
        /\ localDone' = TRUE /\ localDrops' = localDrops + 1 /\ pc' = "saved"
        /\ UNCHANGED <<remoteDone, remoteDrops, pushes, builds, restarts>>

\* "Dein Drop ist da"
Push == /\ pc = "saved"
        /\ (FIXED => remoteDone)
        /\ pushes' = pushes + 1 /\ pc' = "idle"
        /\ UNCHANGED <<localDone, localDrops, remoteDone, remoteDrops, builds, restarts>>

\* backup.upload_if_changed: may happen at any moment (periodic tick, or soon after a nudge)
Upload == /\ remoteDone' = localDone /\ remoteDrops' = localDrops
          /\ UNCHANGED <<localDone, localDrops, pc, pushes, builds, restarts>>

\* deploy / platform restart / OOM: local disk and all threads are gone, boot restores the last upload
Restart == /\ restarts < MaxRestarts
           /\ localDone' = remoteDone /\ localDrops' = remoteDrops
           /\ pc' = "idle" /\ restarts' = restarts + 1
           /\ UNCHANGED <<remoteDone, remoteDrops, pushes, builds>>

Next == StartBuild \/ Save \/ Push \/ Upload \/ Restart

Spec == Init /\ [][Next]_vars

AtMostOnePush     == pushes <= 1                    \* the user is told "your drop is here" once a day
PushedDropVisible == pushes >= 1 => localDrops >= 1 \* who opens the app from the push finds the drop
OneVisibleDrop    == localDrops <= 1
====
