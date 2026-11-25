# DESIGN.md — Emebet Bijigdu Mode (75s Heritage Short)

## 1. Creative Vision & Target Audience
- **Subject:** Emebet Bijigdu Mode (`እመቤት ቢጅግዱ ሞዴ`), a revered and generous governor remembered in living family and civic history.
- **Historical & Geographic Setting:** **Wellega Awraja, Guduru Malole Warada** (`ወለጋ አውራጃ፣ ጉዱሩ ማሎሌ ወረዳ`).
- **Target Audience:** Ethiopian heritage audiences, younger generations connecting with oral history, and viewers of short-form cultural documentaries.
- **Viewing Context:** Mobile and desktop short-form heritage storytelling (75 seconds, 10 shots) anchored by expressive Amharic narration, period-authentic keyframes, subtle motion, and an atmospheric score.
- **Core Emotional Takeaway:** By the end of the film, viewers should feel the rare combination of dignified civic authority, cultural rootedness in Guduru Malole, and open-handed generosity that defined Emebet Bijigdu Mode's leadership.

---

## 2. Audience Test #1 — Radio Cut (`outputs/final/radio_cut.mp4`)

### Test Setup
- **Format Tested:** 75-second assembled Amharic narration radio cut (`radio_cut.mp4`) played end to end before generating final visuals.
- **Participants:** 3 listeners, including a direct primary family source (Emebet Bijigdu Mode's daughter) and 2 general heritage listeners.

### Listener Feedback
- **Audience 1 (Daughter of Emebet Bijigdu Mode):**
  - *Geographic & Administrative Setting:* Insisted on explicitly naming the place of the story: **Wellega Awraja, Guduru Malole Warada** (`ወለጋ አውራጃ፣ ጉዱሩ ማሎሌ ወረዳ`).
  - *Title of Honor:* Recommended addressing her as **"Emebet Bijigdu Mode"** (`እመቤት ቢጅግዱ ሞዴ`) rather than simply "Bijigdu Mode," reflecting the honor and respect she held as governor across the entire area.
  - *Regalia & Armament:* Noted that she wore a traditional ceremonial cloak (**"Kaba"** / ካባ), a full ammunition belt (**"Zinar"** / ዝናር), and her own **pistol**.
  - *Mule & Acoustic Signature:* Her mule was decorated with **silver chains** whose melodic chiming alerted townspeople whenever Emebet Bijigdu Mode was passing through the city.
  - *Tangible Generosity:* Townsfolk facing financial or life hardship could approach her freely and receive **one cow and one ox** to multiply and rebuild a stable livelihood, supplemented with traditional Ethiopian currency (**"Xegera"** / ጠገራ ብር).
- **Audience 2 (General Listener):**
  - Responded emotionally to the narration and clearly understood Emebet Bijigdu Mode's generosity and standing.
- **Audience 3 (General Listener):**
  - Shared the same emotional resonance as Audience 2, confirming that the 75-second story arc and emotional tone land effectively.

---

## 3. Storyboard, Narration & Visual Revisions Before Phase 2

### Narration & Script Updates (`storyboard.json` -> `narration.py`)
1. **Place & Historical Anchoring:** Explicitly name **Wellega Awraja, Guduru Malole Warada** (`ወለጋ አውራጃ፣ ጉዱሩ ማሎሌ ወረዳ`) early in the narration so the story is firmly rooted in its true location.
2. **Honorific Consistency:** Update references from "Bijigdu Mode" to **"Emebet Bijigdu Mode"** (`እመቤት ቢጅግዱ ሞዴ`) across the Amharic narration script.
3. **Specifics of Generosity:** Incorporate her open-door support for struggling citizens—granting **one cow and one ox** to establish self-sustaining livelihoods alongside **Xegera** (`ጠገራ`) currency—while keeping total runtime within the 75-second budget.

### Visual & Audio Design Updates (`storyboard.json` -> Phase 2 Keyframes, Motion & Score)
1. **Setting & Landscape Continuity:** Ground exterior and town shots in the highland landscape and historic town character of **Guduru Malole Warada, Wellega Awraja**.
2. **Costume & Prop Continuity:** Update character visual prompts so Emebet Bijigdu Mode wears a ceremonial **Kaba**, a **Zinar** ammunition belt, and her personal **pistol**.
3. **Ceremonial Mule Detail:** Depict her mule adorned with **ornate silver chains** in city procession shots.
4. **Foley / Score Cue:** Layer a subtle **metallic silver-chain chime** into the procession sound design so viewers hear her arrival the way townspeople did.
5. **Pacing Preservation:** Retain the overall 10-shot rhythm and emotional cadence validated by Listeners 2 and 3.
