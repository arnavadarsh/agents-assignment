# Visual Logic Flow

## Decision Tree

```
┌─────────────────────────────────────────────────┐
│         User Speaks (VAD Detection)             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│      STT Transcribes User Input                 │
│      Example: "yeah", "wait", "yeah ok"         │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  IntelligentInterruptionHandler.should_interrupt│
│      (user_input, agent_speaking)               │
└──────────────────┬──────────────────────────────┘
                   │
          ┌────────┴─────────┐
          │                  │
          ▼                  ▼
    Agent Silent?      Agent Speaking?
          │                  │
          │                  │
    ┌─────▼────────┐   ┌────▼──────────────────────┐
    │ PROCESS      │   │ Analyze Input             │
    │ as normal    │   └────┬──────────────────────┘
    │ input        │        │
    └──────────────┘        │
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Contains │  │ Only     │  │ Mixed    │
        │ interrupt│  │ ignore   │  │ content? │
        │ words?   │  │ words?   │  │          │
        └────┬─────┘  └────┬─────┘  └────┬─────┘
             │             │              │
             │ YES         │ YES          │ YES
             │             │              │
             ▼             ▼              ▼
        ┌─────────┐  ┌──────────┐  ┌──────────┐
        │INTERRUPT│  │  IGNORE  │  │INTERRUPT │
        │Agent    │  │ Continue │  │ Agent    │
        │stops    │  │ speaking │  │ stops    │
        └─────────┘  └──────────┘  └──────────┘
             │             │              │
             │             │ EARLY RETURN │
             │             │ NO PAUSE!    │
             ▼             ▼              ▼
```

## State-Based Behavior Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIGENT INTERRUPTION LOGIC                │
├──────────────┬────────────┬──────────────┬─────────────────────┤
│  USER INPUT  │ AGENT STATE│   DECISION   │      REASON         │
├──────────────┼────────────┼──────────────┼─────────────────────┤
│              │            │              │                     │
│  "yeah"      │  Speaking  │  ← IGNORE    │  Backchanneling     │
│  "ok"        │  Speaking  │  ← IGNORE    │  User listening     │
│  "hmm"       │  Speaking  │  ← IGNORE    │  Acknowledgement    │
│  "uh-huh"    │  Speaking  │  ← IGNORE    │  Passive response   │
│              │            │              │                     │
├──────────────┼────────────┼──────────────┼─────────────────────┤
│              │            │              │                     │
│  "wait"      │  Speaking  │  → INTERRUPT │  Stop command       │
│  "stop"      │  Speaking  │  → INTERRUPT │  Active control     │
│  "no"        │  Speaking  │  → INTERRUPT │  Disagreement       │
│  "hold on"   │  Speaking  │  → INTERRUPT │  User needs pause   │
│              │            │              │                     │
├──────────────┼────────────┼──────────────┼─────────────────────┤
│              │            │              │                     │
│  "yeah wait" │  Speaking  │  → INTERRUPT │  Contains command   │
│  "ok but..."  │  Speaking  │  → INTERRUPT │  Mixed with content │
│              │            │              │                     │
├──────────────┼────────────┼──────────────┼─────────────────────┤
│              │            │              │                     │
│  "yeah"      │  Silent    │  → PROCESS   │  Valid answer       │
│  "ok"        │  Silent    │  → PROCESS   │  Affirmation        │
│  "sure"      │  Silent    │  → PROCESS   │  Agreement          │
│              │            │              │                     │
├──────────────┼────────────┼──────────────┼─────────────────────┤
│              │            │              │                     │
│  "hello"     │  Silent    │  → PROCESS   │  Normal input       │
│  "I need..." │  Silent    │  → PROCESS   │  User request       │
│              │            │              │                     │
└──────────────┴────────────┴──────────────┴─────────────────────┘
```

## Code Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    agent_activity.py                          │
│                                                               │
│  def _interrupt_by_audio_activity(self) -> None:            │
│      opt = self._session.options                             │
│                                                               │
│      # Get current transcript from STT                       │
│      current_transcript = self._audio_recognition.current_transcript
│                                                               │
│      # NEW LOGIC: Use intelligent handler                    │
│      if opt.interruption_handler is not None:               │
│          agent_speaking = (                                  │
│              self._current_speech is not None               │
│              and not self._current_speech.interrupted       │
│          )                                                   │
│                                                               │
│          decision = opt.interruption_handler.should_interrupt(
│              user_input=current_transcript,                  │
│              agent_speaking=agent_speaking                   │
│          )                                                   │
│                                                               │
│          if not decision.should_interrupt:                  │
│              return  # ← CRITICAL: Early return!            │
│                      # Agent continues without pause         │
│                                                               │
│      # Original interruption logic (only reached if above   │
│      # returns True or handler is None)                     │
│      self._current_speech.interrupt()                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│               interruption_handler.py                         │
│                                                               │
│  def should_interrupt(                                       │
│      self,                                                   │
│      user_input: str,                                        │
│      agent_speaking: bool                                    │
│  ) -> InterruptionDecision:                                  │
│                                                               │
│      if not agent_speaking:                                 │
│          return InterruptionDecision(                        │
│              should_interrupt=True,                          │
│              reason="Agent silent - process normally"        │
│          )                                                   │
│                                                               │
│      # Agent IS speaking - apply filters                    │
│      interrupt_matches = find_matches(                       │
│          text, interrupt_patterns                            │
│      )                                                       │
│      if interrupt_matches:                                  │
│          return InterruptionDecision(                        │
│              should_interrupt=True,                          │
│              reason=f"Contains: {interrupt_matches}"         │
│          )                                                   │
│                                                               │
│      ignore_matches = find_matches(                          │
│          text, ignore_patterns                               │
│      )                                                       │
│      all_words = extract_words(text)                         │
│                                                               │
│      if len(ignore_matches) == len(all_words):              │
│          return InterruptionDecision(                        │
│              should_interrupt=False,  # ← IGNORE!           │
│              reason="Pure backchanneling"                    │
│          )                                                   │
│                                                               │
│      return InterruptionDecision(                            │
│          should_interrupt=True,                              │
│          reason="Mixed content"                              │
│      )                                                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Timeline Diagram

```
Time ──────────────────────────────────────────────────────────▶

Agent:  "The history of computers began in the 1940s..."
        ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
        (speaking continuously)
             │
             │
User:        └──► "yeah"
                   │
                   ▼
             ┌──────────────┐
             │ VAD detects  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ STT: "yeah"  │
             └──────┬───────┘
                    │
                    ▼
             ┌─────────────────────┐
             │ Handler checks:     │
             │ - Agent speaking? ✓ │
             │ - Only "yeah"? ✓    │
             │ - Decision: IGNORE  │
             └──────┬──────────────┘
                    │
                    ▼
             ┌──────────────┐
             │ Early return │
             │ No interrupt │
             └──────────────┘
                    
Agent:  "...and continued through the development of..."
        ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
        (NO PAUSE - seamless continuation!)

═══════════════════════════════════════════════════════

Agent:  "The process involves..."
        ■■■■■■■■■■■■■■■■■■■■■■■■■
             │
User:        └──► "wait"
                   │
                   ▼
             ┌──────────────┐
             │ VAD detects  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────┐
             │ STT: "wait"  │
             └──────┬───────┘
                    │
                    ▼
             ┌──────────────────────┐
             │ Handler checks:      │
             │ - Agent speaking? ✓  │
             │ - Contains "wait"? ✓ │
             │ - Decision: INTERRUPT│
             └──────┬───────────────┘
                    │
                    ▼
             ┌──────────────┐
             │ Interrupt!   │
             └──────────────┘

Agent:  [STOPS IMMEDIATELY]
        ■ (interrupted)
```

## Word Categorization

```
╔══════════════════════════════════════════════════════╗
║              IGNORE WORDS (20+)                      ║
║  When agent is speaking → CONTINUE                   ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Acknowledgements:    yeah, ok, okay, sure, yep      ║
║  Affirmations:        right, aha, gotcha, alright    ║
║  Fillers:             hmm, mmm, uh, um, er, ah       ║
║  Compounds:           uh-huh, mm-hmm, mhm            ║
║                                                      ║
╚══════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════╗
║            INTERRUPT WORDS (10+)                     ║
║  When agent is speaking → STOP                       ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Stop commands:       wait, stop, pause, hold on     ║
║  Negation:           no, cancel, never mind          ║
║  Phrases:            hold up, hang on                ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
```

## Success Indicators

```
┌────────────────────────────────────────────────────┐
│  ✅ SCENARIO 1: Long Explanation                  │
│                                                    │
│  Input:  "yeah" while agent speaking              │
│  Output: Agent continues WITHOUT pause            │
│  Status: ✅ PASS                                   │
│                                                    │
│  Evidence: Early return in code prevents          │
│            interruption entirely                   │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  ✅ SCENARIO 2: Passive Affirmation               │
│                                                    │
│  Input:  "yeah" while agent silent                │
│  Output: Agent processes as answer                │
│  Status: ✅ PASS                                   │
│                                                    │
│  Evidence: agent_speaking=False → always process  │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  ✅ SCENARIO 3: The Correction                    │
│                                                    │
│  Input:  "wait" while agent speaking              │
│  Output: Agent stops immediately                  │
│  Status: ✅ PASS                                   │
│                                                    │
│  Evidence: Interrupt word match → interrupt       │
└────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────┐
│  ✅ SCENARIO 4: Mixed Input                       │
│                                                    │
│  Input:  "yeah wait" while agent speaking         │
│  Output: Agent stops (detects "wait")             │
│  Status: ✅ PASS                                   │
│                                                    │
│  Evidence: Priority to interrupt words            │
└────────────────────────────────────────────────────┘
```

---

**All diagrams represent the actual implementation in code.**
