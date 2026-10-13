/-!
Abstract model of `pipeline.dedupe` (Python): keep the first item of every key.
The Python code is NOT extracted from this; the model mirrors the loop by hand:

    seen = set(); out = []
    for i in items:
        k = key(i)
        if k in seen: continue
        seen.add(k); out.append(i)
-/

def dedupeAux {α κ : Type} [DecidableEq κ] (key : α → κ) (seen : List κ) : List α → List α
  | [] => []
  | x :: xs =>
    if key x ∈ seen then dedupeAux key seen xs
    else x :: dedupeAux key (key x :: seen) xs

def dedupe {α κ : Type} [DecidableEq κ] (key : α → κ) (l : List α) : List α :=
  dedupeAux key [] l

section
variable {α κ : Type} [DecidableEq κ] (key : α → κ)

/-- Everything produced has a key that was not in `seen`. -/
theorem dedupeAux_fresh (seen : List κ) (l : List α) :
    ∀ y ∈ dedupeAux key seen l, key y ∉ seen := by
  induction l generalizing seen with
  | nil => simp [dedupeAux]
  | cons x xs ih =>
    unfold dedupeAux
    by_cases h : key x ∈ seen
    · simp only [h, ite_true]
      exact ih seen
    · simp only [h, ite_false, List.mem_cons]
      intro y hy
      rcases hy with rfl | hy
      · exact h
      · have := ih (key x :: seen) y hy
        intro hs
        exact this (List.mem_cons_of_mem _ hs)

/-- The output has pairwise distinct keys. -/
theorem dedupeAux_nodup (seen : List κ) (l : List α) :
    ((dedupeAux key seen l).map key).Nodup := by
  induction l generalizing seen with
  | nil => simp [dedupeAux]
  | cons x xs ih =>
    unfold dedupeAux
    by_cases h : key x ∈ seen
    · simp only [h, ite_true]
      exact ih seen
    · simp only [h, ite_false, List.map_cons, List.nodup_cons, List.mem_map]
      refine ⟨?_, ih (key x :: seen)⟩
      rintro ⟨y, hy, hk⟩
      exact dedupeAux_fresh key (key x :: seen) xs y hy (hk ▸ List.mem_cons_self)

/-- Idempotence: deduplicating twice is the same as once. -/
theorem dedupeAux_idem (seen : List κ) (l : List α) :
    dedupeAux key seen (dedupeAux key seen l) = dedupeAux key seen l := by
  induction l generalizing seen with
  | nil => simp [dedupeAux]
  | cons x xs ih =>
    by_cases h : key x ∈ seen
    · have : dedupeAux key seen (x :: xs) = dedupeAux key seen xs := by simp [dedupeAux, h]
      rw [this]; exact ih seen
    · have e : dedupeAux key seen (x :: xs) = x :: dedupeAux key (key x :: seen) xs := by simp [dedupeAux, h]
      rw [e]
      have : dedupeAux key seen (x :: dedupeAux key (key x :: seen) xs)
          = x :: dedupeAux key (key x :: seen) (dedupeAux key (key x :: seen) xs) := by simp [dedupeAux, h]
      rw [this, ih (key x :: seen)]

/-- Nothing is lost beyond key collisions: every input has an output item with the same key (or its key was already seen). -/
theorem dedupeAux_complete (seen : List κ) (l : List α) :
    ∀ x ∈ l, key x ∈ seen ∨ ∃ y ∈ dedupeAux key seen l, key y = key x := by
  induction l generalizing seen with
  | nil => simp
  | cons x xs ih =>
    intro z hz
    unfold dedupeAux
    by_cases h : key x ∈ seen
    · simp only [h, ite_true]
      rcases List.mem_cons.mp hz with rfl | hz
      · exact Or.inl h
      · exact ih seen z hz
    · simp only [h, ite_false]
      rcases List.mem_cons.mp hz with rfl | hz
      · exact Or.inr ⟨z, List.mem_cons_self, rfl⟩
      · rcases ih (key x :: seen) z hz with h1 | ⟨y, hy, hk⟩
        · rcases List.mem_cons.mp h1 with e | e
          · exact Or.inr ⟨x, List.mem_cons_self, e.symm⟩
          · exact Or.inl e
        · exact Or.inr ⟨y, List.mem_cons_of_mem _ hy, hk⟩

theorem dedupe_idem (l : List α) : dedupe key (dedupe key l) = dedupe key l := dedupeAux_idem key [] l
theorem dedupe_nodup (l : List α) : ((dedupe key l).map key).Nodup := dedupeAux_nodup key [] l
end

/-! The theorems above hold for EVERY key function, including the one that caused bug F1:
the algorithm was right, the key was wrong. With the old key every caption-less post gets the same key
and the "correct" algorithm throws them away: -/
example : dedupe (fun (s : String × Nat) => s.1) [("Bild-Post", 1), ("Bild-Post", 2), ("Bild-Post", 3)] = [("Bild-Post", 1)] := by decide
/-- With a key that includes the URL (the fix) all three survive. -/
example : dedupe (fun (s : String × Nat) => s) [("Bild-Post", 1), ("Bild-Post", 2), ("Bild-Post", 3)]
    = [("Bild-Post", 1), ("Bild-Post", 2), ("Bild-Post", 3)] := by decide

/-! Ranking: score = base + fb(account) + fb(category). Monotone in the feedback weights. -/
def score (base fbAccount fbCategory : Int) : Int := base + fbAccount + fbCategory

theorem score_mono {b a a' c c' : Int} (ha : a ≤ a') (hc : c ≤ c') : score b a c ≤ score b a' c' := by
  unfold score; omega

/-- The server clamps votes to [-5, 5] (`max(-5, min(5, fb + vote))`): the clamp is monotone in the old value. -/
def clamp5 (x : Int) : Int := max (-5) (min 5 x)
theorem clamp5_mono {x y : Int} (h : x ≤ y) : clamp5 x ≤ clamp5 y := by unfold clamp5; omega
theorem clamp5_bounds (x : Int) : -5 ≤ clamp5 x ∧ clamp5 x ≤ 5 := by unfold clamp5; omega

#print axioms dedupe_idem
#print axioms dedupe_nodup
#print axioms dedupeAux_complete
#print axioms score_mono
#print axioms clamp5_mono
