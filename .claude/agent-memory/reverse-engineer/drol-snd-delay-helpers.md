---
name: Drol SND_DELAY_DOWN / SND_DELAY_UP speaker-click helpers
description: Per-iteration pitch-slide speaker-click emitters at $1091/$109E; use ZP_SFX_CLICK indirect to hit $C030
type: project
---

`SND_DELAY_DOWN` at `$1091` and `SND_DELAY_UP` at `$109E` are 13-byte
paired routines that emit X speaker clicks with a sliding per-click
delay.  Both take A=starting pitch, X=click count, clobber A/X/Y.

**The click is `CMP (ZP_SFX_CLICK),Y` with Y=$00.**  ZP $36/$37 is
the ZP_SFX_CLICK pointer: $37=$C0 (boot-time), $36 toggles between
$30 (→ $C030 speaker) and $20 (→ $C020 silent cassette) via Ctrl-S
mute.  So `CMP ($36),Y` with Y=0 reads from $C0XX, which is how the
routine toggles the speaker without STA on a soft-switch.

Per iteration structure (DOWN variant; UP identical but CLC/ADC):

```
TAY          ; Y <- current pitch
SEC/CLC
SBC/ADC #$01 ; A += / A -=  (next iteration's delay)
.inner: DEY; BNE .inner   ; Y-count delay
CMP (ZP_SFX_CLICK),Y      ; click (Y=0)
DEX; BNE outer            ; X-count iterations
```

DOWN shrinks the delay each iteration -> perceived pitch rises.
UP grows the delay each iteration -> perceived pitch falls.

Callers pass A>X so the inner Y-delay never underflows.  10+ call
sites across drol.bin: enemy-C click ($8986 doc: SND_DELAY_DOWN X=$08),
rescue step ($6915 doc: SND_DELAY_UP X=$0A A=$0C), special-slot
sound ($12999 doc: SND_DELAY_UP X=$0A), row-copy-click at $01BE
(SND_DELAY_UP X=4 A=X/4), etc.

**Why this is easy to misread:** the bytes $1091-$10AA used to sit
inside a larger "ENEMY_AI_1" hex blob at $0F5D.  They are NOT part
of enemy AI — they are the bottom tail of a shared drawing routine.
The $0F5D setup routine ends at $1090 with a RTS; $1091 begins a
wholly independent sound utility.

**How to apply:** when you see `JSR $1091` / `JSR $109E` replace
with `JSR SND_DELAY_DOWN` / `JSR SND_DELAY_UP`.  ZP_SFX_CLICK=$36
is the mute pointer — do not confuse with $5C (ROW_COPY_CLICK's
scratch X save) or $F8 (beam sound counter).
