# Updated skin loading and memory test

The storage optimization reduced observed memory use, but loading became slower.
The updated 2x package fails the existing 30-second initialization budget.
This is a measured performance regression, despite passing artwork and animation
equivalence checks. Neither skin was installed or deployed into the running setup.

| Skin | Prior initialization | Updated initialization | Prior working set | Updated working set |
| --- | ---: | ---: | ---: | ---: |
| 1x | 8.27 s | 16.48 s | 518.1 MiB | 347.1 MiB |
| 2x | 29.55 s | 38.38 s | 1805.4 MiB | 1130.3 MiB |

1x used 171.0 MiB less working memory (about 33%); 2x used 675.1 MiB less
(about 37%). Initialization increased 8.21 s and 8.83 s respectively. Working-set
samples were taken 8.5 seconds after CLI autoplay readiness. Exact peak/ready/private
memory fields and package/runtime hashes are in storage-load-benchmark.json;
prior measured hashes/results remain unchanged in info-load-benchmark.json.

Both exact requested skins loaded without logged theme errors or fallback and
stayed alive through the startup observation. The benchmark deliberately returned
a failure status for 2x rather than raising its budget or treating successful
theme parsing as a passing initialization time.

The user authorized this native loading-only test. Each player ran from a copied
full installed VLC runtime with adjacent portable directory, fresh per-scale
config/APPDATA/LOCALAPPDATA/TEMP and a generated silent WAV with dummy audio.
Windows desktops were private and never switched to input. No mouse/keyboard,
focus control or effects helper was used. PID ownership of both TCP listener and
established connection was verified before any loopback RC write; commands only
queried CLI autoplay readiness and quit the owned test player.

Both owned test players closed. The companion, running 1x VLC and pinned helper
retained their process creation identities and stayed alive. All 16 guarded paths
(11 existing) retained their before/after hashes; the input desktop was unchanged.
The other agent held runtime restarts during the test and was notified after
cleanup/preservation checks, before continuing its deployment work.

These are one warm-cache run per scale, not repeated distributions or cold-boot
measurements. The prior run had concurrent headless VLC work; this run had the
other agent doing offline development. Comparisons describe these observed runs,
not a controlled causal experiment. More standalone PNGs are a plausible startup
cost: 1x decoding files increased 8→143 and 2x 34→200. This is a hypothesis until a
balanced-atlas candidate is measured. Larger batching could regain startup speed
at some memory cost; no new candidate or live change was made during this test.

Native animation smoothness, visual controls, tooltip stacking, sound and full
parity acceptance remain unverified for these exact packages. This loading test
does not supersede the existing scoped GUI/audio reports.
