# Project Aegis — Ransomware Detection & Enforcement Execution Layer
## From zero to a measured, verifier-safe Linux eBPF vertical slice

> **Scope**
>
> This document describes the **defensive ransomware execution layer** of Project Aegis: filesystem telemetry, entropy sensing, behavioral signals, canaries, risk accumulation, detect-then-deny enforcement, safety rails, testing, and measurement.
>
> It does **not** provide ransomware payloads, destructive deployment logic, persistence, credential theft, lateral movement, or instructions for attacking real systems.
>
> All destructive-looking experiments in this document operate on a synthetic corpus inside a disposable VM.

---

# 0. What “execution layer” means in Aegis

The ransomware layer is the runtime path that turns low-level filesystem activity into one of four outcomes:

```text
                   FILESYSTEM ACTIVITY
                           |
                           v
              +---------------------------+
              | Kernel observation hooks  |
              +-------------+-------------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
     content sensor                 behavior sensor
     vfs_write                     BPF LSM + metadata
             |                             |
             +--------------+--------------+
                            |
                            v
                   per-process state
                            |
                            v
                    evidence fusion
                            |
                            v
                    decayed risk score
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
       observe           heightened         restrict
          |                 |                  |
          +-----------------+------------------+
                            |
                            v
                           kill
                            |
               +------------+-------------+
               |                          |
               v                          v
      bpf_send_signal(SIGKILL)      LSM returns -EPERM
               |                          |
               +------------+-------------+
                            |
                            v
                      user-space agent
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
      cgroup.kill       forensics         incident record
```

The source project defines the same architectural split:

- content is sampled at `vfs_write`;
- behavioral activity is observed through LSM filesystem hooks;
- canaries provide a high-signal tripwire;
- risk is accumulated in a per-process map;
- once the threshold is crossed, the design uses **detect-then-deny** rather than claiming that the already-entering write can be retroactively cancelled.

---

# 1. Definition of done

The ransomware execution layer is complete enough for a review when the following are all true.

| ID | Requirement | Demonstration |
|---|---|---|
| R1 | `vfs_write` telemetry works | PID, TGID, executable identity, inode, byte count appear in ring-buffer logs |
| R2 | Entropy reference implementation exists | Python/C reference produces repeatable values on text, JPEG, ZIP, random data, and encrypted copies |
| R3 | In-kernel entropy path works or has an explicit fallback | BPF computes bounded fixed-point entropy, or kernel sends bounded samples to user space if the spike fails |
| R4 | Behavioral LSM hooks work | canary write/rename/unlink and normal file operations produce events |
| R5 | Canary manager works | touching a canary raises a high-confidence evidence event |
| R6 | Risk engine works | multiple evidence types accumulate into one per-process decayed score |
| R7 | Detect-then-deny works | crossing the kill threshold marks the PID quarantined, sends SIGKILL, and blocks subsequent writes |
| R8 | Monitor mode is safe | no kill occurs; a `would_kill` event is emitted instead |
| R9 | Never-kill policy works | PID 1, kernel threads, Aegis, and protected services are never selected for enforcement |
| R10 | False-positive evaluation exists | compilers, archive/compression tools, package operations, photo import, backups, database maintenance |
| R11 | Files-lost-before-block is measured | first malicious-like action to enforcement decision is measurable |
| R12 | Reproducibility exists | kernel, CPU/VM, git commit, seed, workload, configuration, and corpus hash are recorded |

The source review slice specifically calls out D1-D6: entropy, canaries, a per-process score, detect-then-deny, measured damage/false positives/overhead, and safety rails.

---

# 2. Design principles

## 2.1 Kernel decides fast; user space decides carefully

Keep the BPF path bounded:

- no dynamic allocation;
- no unbounded strings;
- no unbounded loops;
- no file contents written to persistent logs;
- no complicated parsing;
- no floating-point calculations;
- no expensive hashing on every write.

Push slow work to `aegisd`:

- policy parsing;
- SHA-256;
- forensic snapshots;
- incident graph creation;
- model loading;
- report generation;
- canary generation;
- long-term persistence.

## 2.2 State lives in maps

BPF programs should be mostly reusable logic over shared state:

```text
proc_state
canary_set
trusted_exe
file_class
nlog2n_tab
policy
counters
events
```

This lets the same ransomware detector adapt its sampling behavior without rebuilding or reloading the BPF program.

## 2.3 Fail open

Any of these should resolve to:

```text
ALLOW + increment health/error counter
```

rather than:

```text
KILL
```

Examples:

- missing map entry;
- ring-buffer reserve failure;
- sample copy failure;
- unknown executable;
- unsupported hook;
- stale state;
- malformed policy;
- unavailable PMU signal;
- agent communication failure.

## 2.4 Never use process name as identity

Do not trust:

```text
comm == "backupd"
```

Prefer executable identity derived from:

```text
(device, inode)
```

and, in user space, a SHA-256 digest of the executable.

## 2.5 Separate content detection from enforcement

This split is fundamental:

```text
vfs_write
    |
    +--> content available
    |       |
    |       +--> entropy / sample-based features
    |
    +--> risk update

LSM file_permission
    |
    +--> no write buffer
    +--> behavioral decision
    +--> allow / deny

```

A BPF LSM `file_permission` hook can enforce a policy but does not magically expose the entire write buffer.

---

# 3. Threat model for this layer

## In scope

1. Unprivileged local software modifying user files at scale.
2. Encryptor-like behavior represented safely using legitimate tools or generated workloads.
3. Read → transform → overwrite / create-new → delete-original patterns.
4. Rename/extension churn.
5. Canary modification.
6. High-entropy write bursts.
7. Low-and-slow file modification.
8. Partial-file transformations.
9. Unknown executables or executables launched from suspicious locations.
10. Processes carrying Aegis lineage taint.

## Out of scope

1. An attacker with kernel-level code execution.
2. A malicious kernel module that bypasses the BPF/LSM layer.
3. A fully compromised boot chain.
4. Reconstructing ransomware from encrypted samples.
5. Running real ransomware against real user files.

## Important interpretation

Aegis does not attempt to prove:

> “This process is mathematically ransomware.”

Instead, it detects a combination of behaviors strongly associated with **data-encryption-for-impact-like activity** and moves through a safety-controlled enforcement ladder.

---

# 4. Observable signal model

The source plan defines the ransomware layer around a multi-view evidence set.

| ID | Signal | Main hook/source | Interpretation |
|---|---|---|---|
| S1 | High-entropy write | `vfs_write` sample | Content looks statistically random |
| S2 | Entropy jump | file-class state + write sample | A previously low-entropy file changes toward high entropy |
| S3 | Header destruction | first-byte/class state | File identity/magic disappears or is replaced |
| S4 | Canary hit | BPF LSM hooks | A protected synthetic file was modified |
| S5 | File/dir rate | process counters | One process modifies many distinct files/dirs |
| S6 | Extension churn | rename hook | Repeated bulk renames |
| S7 | Ransom-note pattern | create/open activity | Repeated note-like filename creation |
| S8 | Backup tamper | watched paths + command context | Snapshot/backup destruction behavior |
| S9 | Read → overwrite → unlink | file/process behavior | Typical transformation workflow |
| S10 | Context | lineage/trust/location | Taint, unknown executable, temporary/download origin |

### Important rule

**Do not make S1 alone the kill condition.**

High entropy is normal in:

- JPEG/PNG;
- ZIP/GZIP;
- compressed archives;
- encrypted containers;
- media formats;
- some databases and binary formats.

The primary novelty is the fusion of signals and the cross-layer risk response.

---

# 5. Runtime architecture

```text
                         +----------------------+
                         |      aegisctl         |
                         +----------+-----------+
                                    |
                                    | Unix socket
                                    v
+----------------------------------------------------------------+
|                          aegisd                                |
|                                                                |
|  loader  policy  event-consumer  canary  forensics  incident   |
+----------------------+--------------------------+---------------+
                       |                          |
                       | ringbuf                  | map updates
                       v                          v
+----------------------------------------------------------------+
|                        Kernel / eBPF                            |
|                                                                |
|  +-----------+   +-------------+   +-------------------------+ |
|  | vfs_write |   | BPF LSM     |   | process/file state      | |
|  | entropy   |   | behavior    |   | proc_state / canaries   | |
|  +-----+-----+   +------+------+   +------------+------------+ |
|        |                |                       |              |
|        +----------------+-----------------------+              |
|                             |                                  |
|                             v                                  |
|                       risk engine                              |
|                             |                                  |
|                 +-----------+-----------+                      |
|                 |                       |                      |
|                 v                       v                      |
|             allow/log               quarantine                |
+----------------------------------------------------------------+
```

---

# 6. Repository layout

Recommended repository:

```text
aegis/
├── README.md
├── Makefile
├── config/
│   └── aegis.yaml
│
├── bpf/
│   ├── vmlinux.h
│   ├── common.h
│   ├── maps.h
│   ├── events.h
│   ├── p2_fs.bpf.c
│   ├── p2_lsm.bpf.c
│   ├── risk.bpf.h
│   └── entropy.bpf.h
│
├── agent/
│   ├── main.c
│   ├── loader.c
│   ├── events.c
│   ├── policy.c
│   ├── canary.c
│   ├── forensics.c
│   └── enforce.c
│
├── lib/
│   └── entropy_ref.c
│
├── tools/
│   ├── build_entropy_table.py
│   ├── make_corpus.py
│   ├── safe_encryptor_like.py
│   └── analyze_runs.py
│
├── tests/
│   ├── unit/
│   ├── differential/
│   ├── integration/
│   └── safety/
│
├── eval/
│   ├── protocol.md
│   ├── run.py
│   ├── metrics.py
│   └── plots.py
│
└── docs/
    ├── architecture.md
    ├── threat-model.md
    └── ransomware-layer.md
```

---

# 7. Environment from scratch

## 7.1 Recommended environment

Use a disposable Ubuntu VM as the primary development target.

A practical source-plan baseline is:

```text
Ubuntu 24.04
kernel 6.8 series
BTF enabled
BPF LSM available
ring buffer available
bpf_loop available
```

Treat exact kernel support as a **capability probe**, not an assumption.

## 7.2 Check kernel

```bash
uname -r
```

Expected shape:

```text
6.x.y-...
```

## 7.3 Check BTF

```bash
ls -l /sys/kernel/btf/vmlinux
```

If this path does not exist, the CO-RE workflow cannot proceed normally.

## 7.4 Check BPF LSM

```bash
cat /sys/kernel/security/lsm
```

Look for:

```text
bpf
```

If BPF LSM is unavailable, the system can still operate in reduced detection mode, but pre-emptive LSM denial is unavailable.

## 7.5 Probe BPF helpers/features

```bash
bpftool feature probe kernel | grep -Ei 'bpf_loop|ringbuf|send_signal'
```

## 7.6 Inspect kernel configuration

```bash
grep -E 'BPF_LSM|DEBUG_INFO_BTF|PERF_EVENTS|HID_BPF' \
  /boot/config-$(uname -r)
```

## 7.7 Safety rule

Do not test enforcement on your everyday installation.

Use:

```text
VM snapshot
    |
    +--> clean baseline
    +--> Aegis monitor
    +--> Aegis enforce
    +--> reset snapshot
```

---

# 8. First milestone: prove that `vfs_write` telemetry works

Before entropy, prove the hook.

## 8.1 Minimal event structure

```c
/* bpf/events.h */

struct fs_write_event {
    __u32 pid;
    __u32 tgid;
    __u32 uid;

    __u64 inode;
    __u64 file_dev;

    __u64 count;
    __s64 pos;

    __u64 ts_ns;

    char comm[16];
};
```

## 8.2 Ring buffer

```c
/* bpf/maps.h */

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);
} events SEC(".maps");
```

## 8.3 Minimal BPF sensor

```c
/* bpf/p2_fs.bpf.c */

#include "vmlinux.h"

#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#include "events.h"
#include "maps.h"

char LICENSE[] SEC("license") = "GPL";

#define S_ISREG(m) (((m) & 00170000) == 0100000)

SEC("fentry/vfs_write")
int BPF_PROG(aegis_vfs_write,
             struct file *file,
             const char __user *buf,
             size_t count,
             loff_t *pos)
{
    struct inode *inode;
    struct fs_write_event *e;

    if (!file)
        return 0;

    inode = BPF_CORE_READ(file, f_inode);
    if (!inode)
        return 0;

    if (!S_ISREG(BPF_CORE_READ(inode, i_mode)))
        return 0;

    e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    __u64 pid_tgid = bpf_get_current_pid_tgid();

    e->pid = (__u32)pid_tgid;
    e->tgid = (__u32)(pid_tgid >> 32);
    e->uid = (__u32)bpf_get_current_uid_gid();

    e->inode = BPF_CORE_READ(inode, i_ino);
    e->file_dev = BPF_CORE_READ(inode, i_sb, s_dev);

    e->count = count;
    e->pos = pos ? *pos : 0;
    e->ts_ns = bpf_ktime_get_ns();

    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);

    return 0;
}
```

## 8.4 What this proves

Run:

```bash
printf 'hello\n' >> /tmp/aegis-test.txt
```

You should see an event with:

- PID;
- TGID;
- process name;
- inode;
- device;
- byte count;
- timestamp;
- file offset.

Do not proceed until this path is stable.

---

# 9. Entropy: understand the math before coding the BPF version

For a byte sample of size `N` with byte histogram counts `c_i`:

```text
H = log2(N) - (1/N) * Σ[c_i * log2(c_i)]
```

`H` is measured in bits per byte.

The maximum is:

```text
8 bits/byte
```

but finite samples of uniform random data estimate slightly below 8.

## 9.1 Why sample size matters

The source plan gives approximately:

| Sample N | Approx. finite-sample bias | Random-data H |
|---:|---:|---:|
| 512 | 0.36 | 7.64 |
| 1024 | 0.18 | 7.82 |
| 2048 | 0.09 | 7.91 |
| 4096 | 0.045 | 7.955 |

Therefore:

```text
Do NOT use:
    H > 7.9

as a universal threshold.

```

Instead:

```text
threshold = threshold_for_sample_size(N)
```

---

# 10. Fixed-point entropy for eBPF

eBPF does not provide the same floating-point math environment as Python.

The source design uses:

```text
T[c] = round(c * log2(c) * 2^16)
```

for:

```text
c = 0..4096
```

and:

```text
T[0] = 0
```

Then:

```text
H_q16 = (T[N] - Σ T[c_i]) / N
```

This gives a Q16 fixed-point entropy estimate.

## 10.1 Why Q16

Q16 means:

```text
stored_value = real_value * 65536
```

For example:

```text
7.5 bits/byte

stored ≈ 7.5 * 65536
       ≈ 491520
```

This lets integer arithmetic preserve useful fractional precision.

---

# 11. Generate the lookup table in user space

Use Python during startup/build.

## 11.1 `tools/build_entropy_table.py`

```python
#!/usr/bin/env python3

import math
import struct
from pathlib import Path

MAX_N = 4096
Q = 1 << 16

out = Path("build/nlog2n.bin")
out.parent.mkdir(parents=True, exist_ok=True)

values = []

for c in range(MAX_N + 1):
    if c == 0:
        value = 0
    else:
        value = round(c * math.log2(c) * Q)
    values.append(value)

with out.open("wb") as f:
    for value in values:
        f.write(struct.pack("<I", value))

print(f"wrote {len(values)} entries to {out}")
print(f"size: {out.stat().st_size} bytes")
```

Expected size:

```text
4097 * 4 bytes
≈ 16 KiB
```

## 11.2 Loader responsibility

At startup:

```text
open BPF object
    |
    v
load program
    |
    v
find nlog2n_tab map
    |
    v
for c = 0..4096:
    update map[c]
```

Do not recompute logarithms inside the BPF program.

---

# 12. Miller–Madow correction

The plug-in entropy estimator is biased low for finite samples.

Use:

```text
H_mm = H + (K_obs - 1) / (2N ln 2)
```

where:

```text
K_obs = number of non-zero histogram bins
```

In Q16, the correction term is approximately:

```text
(K_obs - 1) * 47274 / N
```

The exact constant should be generated and shared between:

```text
Python reference
C reference
BPF implementation
```

Do not copy three independently rounded constants.

---

# 13. Pure-function entropy library

Create one implementation that can be compiled in both user space and BPF-compatible unit tests.

## 13.1 `bpf/entropy.bpf.h`

```c
#ifndef AEGIS_ENTROPY_H
#define AEGIS_ENTROPY_H

#include <stdint.h>

#define AEGIS_Q16 (1u << 16)

static __inline uint32_t entropy_miller_madow_q16(
    uint32_t n,
    uint32_t occupied_bins,
    uint32_t correction_const_q16)
{
    if (n == 0)
        return 0;

    if (occupied_bins <= 1)
        return 0;

    return ((occupied_bins - 1) * correction_const_q16) / n;
}

static __inline uint32_t entropy_from_table_q16(
    uint32_t n,
    const uint32_t *table,
    const uint32_t *hist)
{
    uint64_t sum = 0;

    if (n == 0)
        return 0;

    for (uint32_t i = 0; i < 256; i++)
        sum += table[hist[i]];

    uint64_t numerator = table[n] - sum;

    return (uint32_t)(numerator / n);
}

#endif
```

The production BPF implementation should replace pointer-based table access with BPF map lookups.

---

# 14. BPF scratch storage

A 256-bin histogram of 32-bit values cannot safely be placed on the BPF stack.

Use:

```text
BPF_MAP_TYPE_PERCPU_ARRAY
```

for scratch state.

Example concept:

```c
#define SAMPLE_BYTES 4096

struct entropy_scratch {
    __u8  buf[SAMPLE_BYTES];
    __u32 hist[256];

    __u32 n;
    __u32 occupied;
    __u32 entropy_q16;
};
```

Map:

```c
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct entropy_scratch);
} entropy_scratch SEC(".maps");
```

The source design deliberately keeps large scratch state in map memory and scalar control values on the BPF stack.

---

# 15. Safe sample extraction

The content hook should have cheap gates first.

Recommended gate order:

```text
1. current process valid?
2. file valid?
3. regular file?
4. write size >= minimum?
5. process not trusted?
6. sample rate says "sample"?
7. scratch map available?
8. user-buffer copy succeeds?
9. histogram
10. entropy
11. risk update
12. emit only meaningful events
```

This order matters because the expensive path should not run for every tiny write.

---

# 16. `bpf_loop` strategy

The source design proposes `bpf_loop` for bounded loops such as:

```text
4096 sample bytes
256 histogram bins
```

Conceptual flow:

```text
bpf_loop(4096):
    byte = scratch->buf[index]
    scratch->hist[byte]++

bpf_loop(256):
    count = hist[index]
    table_value = nlog2n_tab[count]
    sum += table_value
```

Use a power-of-two sample size:

```text
4096
2048
1024
512
```

because:

```text
index & (SAMPLE_BYTES - 1)
```

is verifier-friendly.

---

# 17. Entropy BPF control-flow skeleton

The production code should follow this structure.

```c
SEC("fentry/vfs_write")
int BPF_PROG(p2_entropy_write,
             struct file *file,
             const char __user *ubuf,
             size_t count,
             loff_t *pos)
{
    struct proc_state *ps;
    struct entropy_scratch *sc;
    __u32 zero = 0;
    __u32 sample_n;

    /* 1. Basic validation */
    if (!file || !ubuf)
        return 0;

    /* 2. Regular-file gate */
    struct inode *inode = BPF_CORE_READ(file, f_inode);
    if (!inode)
        return 0;

    if (!S_ISREG(BPF_CORE_READ(inode, i_mode)))
        return 0;

    /* 3. Minimum size */
    if (count < MIN_SAMPLE_BYTES)
        return 0;

    /* 4. Process state */
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 tgid = pid_tgid >> 32;

    ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
    if (!ps)
        return 0;

    /* 5. Trust gate */
    if (ps->flags & TRUSTED_EXE)
        return 0;

    /* 6. Sampling gate */
    if (!should_sample(ps))
        return 0;

    /* 7. Scratch */
    sc = bpf_map_lookup_elem(&entropy_scratch, &zero);
    if (!sc)
        return 0;

    sample_n = count;
    if (sample_n > SAMPLE_BYTES)
        sample_n = SAMPLE_BYTES;

    /* 8. Copy */
    long rc = bpf_probe_read_user(sc->buf, sample_n, ubuf);
    if (rc != 0) {
        increment_counter(COUNTER_SAMPLE_COPY_FAIL);
        return 0;
    }

    /* 9. Clear histogram */
    clear_histogram(sc);

    /* 10. Histogram */
    build_histogram(sc, sample_n);

    /* 11. Entropy */
    sc->entropy_q16 = corrected_entropy_q16(sc, sample_n);

    /* 12. Update risk */
    apply_entropy_evidence(ps, sc);

    /* 13. Emit only if interesting */
    maybe_emit_entropy_event(ps, sc);

    return 0;
}
```

This is intentionally a **control-flow template**. Keep your verified kernel-specific helper code inside the marked functions.

---

# 18. Handling `bpf_probe_read_user` failures

Do not assume every user-buffer read succeeds.

Track:

```text
sample_attempts
sample_success
sample_fail
```

Calculate:

```text
failure_rate = sample_fail / sample_attempts
```

Break it down by workload:

```text
compiler
archive tool
database
benchmark
encryptor-like workload
```

If failure rate is unexpectedly high:

1. confirm the problem with a small sample;
2. check the hook context;
3. test a sleepable-capable design where appropriate;
4. test `bpf_copy_from_user` where supported;
5. keep a userspace fallback.

Do not silently treat copy failure as malicious evidence.

---

# 19. Sampling controller

The default system should not sample every write.

A simple model:

```text
sample_shift = 4
```

means:

```text
1 in 2^4 = 1 in 16 writes
```

For heightened risk:

```text
sample_shift = 2
```

means:

```text
1 in 4 writes
```

For a strongly suspicious process:

```text
sample_shift = 0
```

means:

```text
every eligible write
```

The source plan calls this **risk-adaptive sensing**.

Example policy:

```text
baseline:
    1 / 16

TAINT_HID:
    1 / 4

PMU_ANOM:
    1 / 4

CANARY_HIT:
    1 / 1

tier >= restrict:
    1 / 1
```

The exact values are experimental parameters.

---

# 20. File identity model

Do not key canaries by path alone.

Paths can change because of:

- rename;
- directory moves;
- mount namespace changes;
- symlink traversal;
- application behavior.

Recommended kernel key:

```c
struct canary_key {
    __u64 dev;
    __u64 ino;
    __u64 generation;
};
```

For normal files, maintain:

```text
dev
inode
optional generation / version
```

Paths can remain in user-space metadata for human-readable incident reports.

---

# 21. Canary system

## 21.1 Purpose

A canary is deliberately planted synthetic data whose modification is treated as extremely strong evidence.

Desired properties:

- plausible file type;
- realistic content;
- realistic name;
- distributed across important directories;
- not used by normal applications;
- easy for Aegis to identify;
- difficult for generic bulk traversals to avoid.

## 21.2 Recommended types

Examples from the design:

```text
.txt
.docx
.xlsx
.pdf
.jpg
.png
.sqlite
```

Generate valid-looking but synthetic content.

## 21.3 Placement

Example:

```text
~/Documents/.aegis/
~/Documents/ProjectNotes_2019.pdf
~/Desktop/Tax_Archive.xlsx
~/Downloads/Receipt_2024.pdf
```

Do not put canaries directly in system-critical directories.

## 21.4 Rotation

Rotate periodically:

```text
old canaries
    |
    +--> safely remove
    |
new canaries
    |
    +--> register in kernel map
```

Never expose the manifest to ordinary users if doing so would make the experiment meaningless.

---

# 22. Canary events

Every canary action should produce an event such as:

```json
{
  "type": "CANARY_HIT",
  "pid": 1234,
  "tgid": 1234,
  "inode": 918273,
  "dev": 2049,
  "operation": "WRITE",
  "timestamp_ns": 1234567890
}
```

The event should contain evidence metadata, not file contents.

---

# 23. LSM behavioral hooks

Use kernel-version-specific hooks for:

```text
file_permission
inode_rename
inode_unlink
file_open
inode_create
```

Verify exact availability and argument signatures against your target kernel.

## 23.1 What LSM does here

LSM is primarily the:

```text
behavior + enforcement plane
```

It can answer:

```text
Should this operation be allowed?
```

It is not the main entropy-content sensor.

---

# 24. `file_permission` decision path

Conceptual logic:

```text
on file_permission:

    if not regular file:
        ALLOW

    pid = current process

    state = proc_state[pid]

    if state missing:
        ALLOW + error_counter++

    if mode == monitor:
        ALLOW

    if state.quarantined:
        DENY

    if state.tier >= RESTRICT and file not in safe set:
        DENY

    ALLOW
```

Important:

```text
ALLOW on map miss
```

is deliberate.

---

# 25. Rename/unlink behavioral hooks

A ransomware-like workload often follows:

```text
read original
    |
write transformed copy
    |
rename transformed file
    |
unlink original
```

or:

```text
open original
write transformed content in-place
rename extension
```

Record:

```text
pid
tgid
source inode
destination inode when available
operation
timestamp
process identity
```

Do not store full file contents.

---

# 26. Extension churn

Do not classify every rename as malicious.

Track a rolling window.

Example feature:

```text
rename_count_100ms
rename_count_1s
unique_source_extensions
unique_destination_extensions
```

Then derive:

```text
extension_churn_score
```

from the relationship among those values.

Example conceptual rule:

```text
if:
    many distinct files renamed
    AND destination extension is repeatedly transformed
    AND file breadth is high
then:
    add EXT_CHURN evidence
```

This is a feature, not an automatic kill.

---

# 27. File/dir rate

Maintain short rolling buckets.

Source-plan representation:

```c
u16 files_w[10];
u16 dirs_w[10];
u16 renames[10];
u16 unlinks[10];
u16 hi_ent_writes[10];
```

A simple layout:

```text
bucket 0: 0–99 ms
bucket 1: 100–199 ms
...
bucket 9: 900–999 ms
```

Every tick:

```text
bucket = (now / 100ms) % 10
```

Increment:

```text
files_w[bucket]
dirs_w[bucket]
renames[bucket]
unlinks[bucket]
hi_ent_writes[bucket]
```

Use saturating counters:

```c
if (counter != UINT16_MAX)
    counter++;
```

This prevents overflow from becoming a wraparound-to-zero bug.

---

# 28. Decayed risk state

The source plan uses a per-process structure similar to:

```c
struct proc_state {
    __u64 first_seen_ns;
    __u64 last_update_ns;

    __u32 risk_q8;
    __u32 flags;

    __u32 taint_src_dev;

    __u32 exe_dev;
    __u64 exe_ino;

    __u16 files_w[10];
    __u16 dirs_w[10];
    __u16 renames[10];
    __u16 unlinks[10];
    __u16 hi_ent_writes[10];

    __u16 ent_ewma_q8;

    __u8 tier;
    __u8 sample_shift;
};
```

---

# 29. Fixed-point risk representation

Use:

```text
risk_q8
```

where:

```text
stored = real_score * 256
```

So:

```text
25.0 -> 6400
50.0 -> 12800
80.0 -> 20480
```

This avoids floating-point arithmetic inside BPF.

---

# 30. Risk decay

The source design uses a simple verifier-friendly half-life approximation:

```text
elapsed_ms = (now - last_update) / 1e6

risk = risk >>
       min(elapsed_ms / HALF_LIFE_MS, 31)
```

Then:

```text
risk = min(
    risk + evidence_weight * multiplier,
    RISK_MAX
)
```

This is not the only possible decay function, but it is attractive because it is integer-only and bounded.

---

# 31. Evidence weights

Starting values from the project plan:

| Evidence | Starting weight |
|---|---:|
| Canary write/rename/unlink | +40 |
| Backup/snapshot tamper | +30 |
| Ransom-note pattern | +15 |
| Header destruction | +8 |
| Entropy jump | +5 |
| High-entropy write | +2 |
| Extension churn | +6 |
| File/dir breadth rate | +5 |
| PMU crypto-loop signal | +10 |
| Shell/interpreter from tainted lineage | +10 |
| Untrusted executable from tmp/download | +3 |

These are **starting values**, not final scientific constants.

Tune them only on training/calibration data, then evaluate on held-out data.

---

# 32. Tier thresholds

Starting point:

```text
T1 = 25   heightened
T2 = 50   restrict
T3 = 80   kill
```

The important concept is:

```text
evidence -> score -> tier
```

not:

```text
one heuristic -> kill
```

---

# 33. Context multipliers

Example:

```text
baseline multiplier = 1.00

TAINT_HID = 1.50
PMU_ANOM  = 1.25
```

Cap the multiplier so a bug cannot create an unbounded risk value.

Example:

```c
#define MULT_Q8_BASE 256
#define MULT_Q8_HID  384   /* 1.50 */
#define MULT_Q8_PMU  320   /* 1.25 */

#define MULT_Q8_MAX  512   /* 2.00 */
```

---

# 34. Evidence application

Conceptual helper:

```c
static __always_inline void add_evidence(
    struct proc_state *ps,
    __u32 weight_q8,
    __u32 multiplier_q8,
    __u64 now)
{
    decay_risk(ps, now);

    __u64 delta =
        ((__u64)weight_q8 * multiplier_q8) >> 8;

    __u64 next =
        (__u64)ps->risk_q8 + delta;

    if (next > RISK_MAX_Q8)
        next = RISK_MAX_Q8;

    ps->risk_q8 = (__u32)next;
    ps->last_update_ns = now;
}
```

---

# 35. Why canaries get special treatment

Suppose the process:

```text
writes one canary
```

Aegis should not need ten more independent entropy observations to reach a high-risk state.

A canary is:

```text
high information
low expected benign probability
```

Therefore the project plan gives it:

```text
+40
```

and recommends aggressive escalation when taint or other context is present.

---

# 36. Detect-then-deny sequence

This is the most important execution path.

```text
write enters vfs_write
       |
       v
content/behavior evidence observed
       |
       v
risk crosses T3
       |
       +--> proc_state[pid].QUARANTINED = 1
       |
       +--> bpf_send_signal(SIGKILL)
       |
       +--> KILL_DECISION ringbuf event
       |
       v
race window / later write attempts
       |
       v
BPF LSM file_permission
       |
       +--> QUARANTINED?
               |
               +--> YES: -EPERM
               +--> NO:  ALLOW
       |
       v
aegisd
       |
       +--> cgroup.kill
       +--> forensics
       +--> incident record
```

The source plan explicitly calls out that the first offending write may already have happened before the decision is made.

Therefore the primary damage metric is:

```text
files lost before block
```

not:

```text
zero files modified
```

---

# 37. Kernel-side kill helper

Example shape:

```c
static __always_inline int try_kill_current(
    struct proc_state *ps)
{
    if (!ps)
        return 0;

    if (ps->flags & NEVER_KILL)
        return 0;

    if (!(ps->flags & QUARANTINED))
        return 0;

    return bpf_send_signal(SIGKILL);
}
```

Never put the final policy decision in a scattered set of unrelated hooks.

Centralize:

```text
can_enforce()
should_kill()
should_deny_write()
```

and test them as pure functions wherever possible.

---

# 38. LSM deny logic

Conceptual implementation:

```c
SEC("lsm/file_permission")
int BPF_PROG(aegis_file_permission,
             struct file *file,
             int mask)
{
    if (!file)
        return 0;

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 tgid = pid_tgid >> 32;

    struct proc_state *ps =
        bpf_map_lookup_elem(&proc_state_map, &tgid);

    if (!ps)
        return 0;  /* fail open */

    if (!(ps->flags & QUARANTINED))
        return 0;

    if (is_read_only_mask(mask))
        return 0;

    return -EPERM;
}
```

The exact semantics of `mask` and hook arguments must be verified on your target kernel.

---

# 39. Monitor mode

Never start development in enforce mode.

Modes:

```text
monitor
alert
enforce
learn
```

## Monitor

```text
detect
log
never kill
never deny
```

## Alert

```text
detect
notify
never kill
```

## Enforce

```text
detect
deny / kill
cgroup containment
```

## Learn

```text
observe
collect normal behavior
propose trusted executables/policies
```

---

# 40. Safety rails

These are non-negotiable.

## 40.1 Never-kill list

Protect:

```text
PID 1
kernel threads
aegisd
aegisd children
critical system services
SSH sessions where desired
display server
user-configured critical processes
```

## 40.2 Kill rate limiter

Example:

```text
max 3 process kills / minute
```

When exceeded:

```text
automatic downgrade -> alert
```

This protects against a policy bug causing a desktop-wide failure.

## 40.3 Kill-switch

Provide:

```bash
aegisctl disable
```

and a boot-time policy file that disables enforcement.

## 40.4 Dry-run mode

Every enforcement rule should support:

```text
would_kill
would_deny
would_quarantine
```

---

# 41. Process identity and never-kill checks

Do not rely on:

```text
comm
```

Use a combination of:

```text
TGID
executable device + inode
cgroup
systemd unit
agent identity
```

The source design recommends identifying Aegis itself by:

```text
(executable dev/inode, cgroup, systemd unit)
```

rather than its displayed process name.

---

# 42. Trusted executable model

A trusted program entry should contain:

```text
exe_dev
exe_ino
flags
optional sha256
added_by
timestamp
```

Example conceptual map key:

```c
struct exe_key {
    __u64 dev;
    __u64 ino;
};
```

Value:

```c
struct exe_trust {
    __u32 flags;
    __u64 approved_ns;
    __u8 sha256[32];
};
```

Canary events should **not** be ignored merely because the executable is trusted.

This prevents:

```text
trusted binary abused
        +
canary touched
        =
silently allowed
```

---

# 43. File-class state

Entropy becomes more useful when Aegis remembers what a file looked like before modification.

Example state:

```c
struct file_class_state {
    __u64 dev;
    __u64 ino;

    __u32 class_id;

    __u32 baseline_entropy_q16;
    __u64 last_seen_ns;

    __u8  magic_prefix[16];
    __u8  magic_len;

    __u32 flags;
};
```

Possible flags:

```text
LOW_ENTROPY_BASELINE
COMPRESSED
MEDIA
DATABASE
TEXT_LIKE
UNKNOWN
```

Do not make an aggressive classification permanent. File content can legitimately change.

---

# 44. Entropy jump

Define:

```text
entropy_now
baseline_entropy
delta = entropy_now - baseline_entropy
```

Then:

```text
if baseline is low
and delta is large
and process is modifying many files:
    add S2 evidence
```

This is much more informative than:

```text
if entropy_now > X
```

---

# 45. Header-destruction signal

For recognized file types:

```text
save initial magic/class
```

Later, if:

```text
write starts near offset 0
AND magic no longer matches expected class
```

record:

```text
HDR_DESTROYED
```

Examples of benign caveats:

- some applications legitimately rewrite headers;
- temporary files may not have stable headers;
- databases may update binary headers;
- files may be created empty and populated later.

Therefore:

```text
HDR_DESTROYED should increase risk,
not become a universal kill rule.
```

---

# 46. Backup/snapshot tamper signal

Maintain a configurable watch list.

Examples from the source plan:

```text
/var/backups
/timeshift
/.snapshots
```

and monitor:

```text
unlink
rename
create
open for write
```

Also optionally monitor executions of known administration tools.

Important:

```text
do not hard-code one distro's path assumptions into the core detector
```

Make the policy data-driven.

---

# 47. Safe encryptor-like workload design

Do not write ransomware for testing.

Instead generate the **behavioral shape** safely.

Allowed test workflow:

```text
synthetic corpus
    |
    +--> read file
    |
    +--> transform / compress / encrypt a copy
    |
    +--> write transformed copy
    |
    +--> optional rename
    |
    +--> optional remove original
```

All inside a disposable VM.

Recommended legitimate tools:

```text
openssl
gpg
7z
zip
tar
zstd
```

The goal is to generate file-system patterns, not to reproduce malware internals.

---

# 48. Synthetic corpus generator

Create:

```text
5,000–10,000 files
```

with a realistic mixture:

```text
text
source code
JSON
CSV
PDF
JPEG
PNG
ZIP
small database files
binary blobs
```

Vary sizes:

```text
1 KiB
4 KiB
8 KiB
16 KiB
64 KiB
256 KiB
1 MiB
```

Use deterministic seeds.

---

# 49. `tools/make_corpus.py`

```python
#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import random
from pathlib import Path

ROOT = Path("lab_corpus")
SEED = 1337
COUNT = 5000

rng = random.Random(SEED)

EXTENSIONS = [
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".jpg",
    ".png",
    ".pdf",
    ".zip",
    ".bin",
    ".db",
]

def deterministic_bytes(n: int, seed: int) -> bytes:
    out = bytearray()
    counter = 0

    while len(out) < n:
        h = hashlib.sha256(
            f"{seed}:{counter}".encode()
        ).digest()
        out.extend(h)
        counter += 1

    return bytes(out[:n])

def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)

    for i in range(COUNT):
        ext = rng.choice(EXTENSIONS)
        size = rng.choice([
            1024,
            4096,
            8192,
            16384,
            65536,
            262144,
        ])

        subdir = ROOT / f"d{i % 100:03d}"
        subdir.mkdir(exist_ok=True)

        path = subdir / f"sample_{i:06d}{ext}"

        data = deterministic_bytes(size, i)
        path.write_bytes(data)

    print(f"created {COUNT} synthetic files under {ROOT}")

if __name__ == "__main__":
    main()
```

This generates inert synthetic bytes only.

---

# 50. Safe encryptor-like workload runner

The safest benchmark is to transform **copies** of the corpus.

Example shape:

```text
lab_corpus/
benchmark_output/
```

Never point the tool at:

```text
/home/user
/home/user/Documents
```

or another real-data directory.

---

# 51. Example safe workload modes

Implement workload profiles:

```text
PROFILE_A:
    copy -> high-entropy transformation -> new file

PROFILE_B:
    transform in place on synthetic corpus

PROFILE_C:
    new file -> rename extension -> delete synthetic original

PROFILE_D:
    low-and-slow pacing

PROFILE_E:
    partial-file transformation

PROFILE_F:
    compressed-input-heavy benign workload
```

Each profile is a benchmark label, not malware.

---

# 52. Pseudocode for the safe behavior generator

```text
for synthetic_file in corpus:

    read a bounded chunk

    produce transformed bytes using a standard tool/library

    write transformed data to benchmark_output

    if mode == IN_PLACE:
        replace only the synthetic copy

    if mode == RENAME:
        rename transformed output

    if mode == DELETE_ORIGINAL:
        delete only the synthetic source

    sleep according to profile
```

The evaluation harness should validate that every path belongs to the disposable VM corpus before proceeding.

---

# 53. Benign workload suite

Your detector must survive workloads that naturally look “busy.”

Include:

```text
gcc build
cmake build
git checkout
git clone
tar
zstd
7z
video encoding
photo import
rsync
backup job
database maintenance
package updates
large file copies
```

The source plan specifically calls for false-positive testing against compiler, archive/compression, database, backup, package, git, and photo workflows.

---

# 54. Detection experiment E2

Primary question:

```text
Does multi-signal P2 outperform entropy alone?
```

Compare:

```text
Detector A:
    entropy-only

Detector B:
    entropy
    + canary
    + breadth
    + rename
    + unlink
    + context
```

Keep:

```text
same corpus
same seeds
same VM
same workloads
same measurement method
```

---

# 55. Detection experiment E3

Question:

```text
Does context/taint reduce detection latency?
```

Compare:

```text
run 1:
    no taint

run 2:
    taint enabled
```

Measure:

```text
time to first detection
files lost before block
bytes lost before block
```

The original Aegis architecture uses HID-taint as a future cross-layer signal; the P2 layer should treat the taint flag as optional context and remain useful without it.

---

# 56. Attack-like workload timeline

Example timeline:

```text
t0.000:
    process opens first synthetic file

t0.008:
    writes transformed bytes

t0.015:
    entropy event

t0.028:
    second file modified

t0.041:
    extension rename

t0.055:
    third file modified

t0.090:
    canary modified

t0.091:
    CANARY_HIT

t0.092:
    risk >= T3

t0.092:
    QUARANTINED

t0.093:
    SIGKILL sent

t0.094:
    next write attempt -> -EPERM

t0.100:
    agent consumes decision

t0.120:
    cgroup containment

t0.150:
    incident record complete
```

These are illustrative timestamps only.

Measure your real values.

---

# 57. Files-lost-before-block metric

Define clearly:

```text
files_lost_before_block
=
number of distinct file identities whose contents were modified
before enforcement became effective
```

Store:

```text
decision_ts
effective_deny_ts
```

and count affected synthetic files.

Do not claim:

```text
files lost = 0
```

until the measurement proves it.

---

# 58. Block latency

Report two phases:

```text
detection_latency
    first malicious-like action
        ->
    kill decision

block_latency
    kill decision
        ->
    effective LSM deny
```

This distinguishes:

```text
slow detector
```

from:

```text
fast detector + slow control path
```

---

# 59. Ring-buffer event schema

Recommended common event:

```c
enum aegis_event_type {
    EVT_FS_WRITE = 1,
    EVT_HIGH_ENTROPY,
    EVT_ENTROPY_JUMP,
    EVT_HEADER_DESTROYED,
    EVT_CANARY_HIT,
    EVT_RENAME_CHURN,
    EVT_UNLINK_BURST,
    EVT_BACKUP_TAMPER,
    EVT_RISK_UPDATE,
    EVT_KILL_DECISION,
    EVT_DENY_DECISION,
    EVT_HEALTH,
};
```

Structure:

```c
struct aegis_event {
    __u64 ts_ns;

    __u32 type;
    __u32 pid;
    __u32 tgid;

    __u32 flags;
    __u32 risk_q8;

    __u64 dev;
    __u64 ino;

    __u64 bytes;
    __u32 evidence_q8;
    __u32 aux;

    char comm[16];
};
```

Keep the structure compact.

---

# 60. User-space agent responsibilities

`aegisd` should:

```text
1. load BPF
2. populate policy
3. populate entropy lookup table
4. register canaries
5. consume ring buffer
6. write structured logs
7. handle enforcement actions that require user-space APIs
8. collect forensics
9. build incident records
10. expose status over a root-only Unix socket
```

Do not make the agent part of the critical entropy loop.

---

# 61. Event consumer logic

Conceptual:

```c
static int on_event(void *ctx, void *data, size_t size)
{
    const struct aegis_event *e = data;

    switch (e->type) {

    case EVT_HIGH_ENTROPY:
        handle_entropy(e);
        break;

    case EVT_CANARY_HIT:
        handle_canary(e);
        break;

    case EVT_KILL_DECISION:
        handle_kill_decision(e);
        break;

    default:
        break;
    }

    return 0;
}
```

The handler should never assume:

```text
event arrival == successful enforcement
```

Those are separate state transitions.

---

# 62. Forensics after a decision

When a decision occurs, collect:

```text
/proc/<pid>/cmdline
/proc/<pid>/cwd
/proc/<pid>/exe
parent chain
executable SHA-256
cgroup
open file descriptors where feasible
recent Aegis evidence
risk history
```

Record timestamps.

Do not collect:

```text
raw keyboard data
full file contents
unnecessary secrets
```

---

# 63. Incident record example

```json
{
  "id": "inc-2026-000001",
  "mode": "enforce",
  "decision": {
    "tier": 3,
    "action": "kill",
    "latency_ms": 18
  },
  "process": {
    "pid": 1234,
    "exe": "/opt/lab/benchmark",
    "sha256": "..."
  },
  "evidence": [
    {
      "type": "HIGH_ENTROPY",
      "weight": 2
    },
    {
      "type": "EXT_CHURN",
      "weight": 6
    },
    {
      "type": "CANARY_HIT",
      "weight": 40
    }
  ],
  "files": {
    "modified_before_block": 7
  }
}
```

---

# 64. Privacy boundary

The execution layer should never become a keylogger or data collector.

Do not store:

```text
file contents
raw keyboard content
user secrets
```

Store:

```text
metadata
timing
risk
event types
file identity metadata
hashed executable identity
coarse path information
```

For evaluation exports, support path hashing.

---

# 65. Policy file

Example:

```yaml
version: 1

mode: monitor

never_kill:
  pids:
    - 1
  kernel_threads: true
  units:
    - aegisd.service

kill_rate_limit:
  max_per_minute: 3
  on_exceed: alert_mode

fs:
  sample_bytes: 4096
  min_write_bytes: 512

  baseline_sample_shift: 4
  tainted_sample_shift: 0

  thresholds_q16:
    512: TBD
    1024: TBD
    2048: TBD
    4096: TBD

  tiers:
    heightened: 25
    restrict: 50
    kill: 80

  canary:
    count: 24
    rotate_days: 7

  backup_watch:
    - /var/backups
    - /timeshift
    - /.snapshots

logging:
  format: jsonl
  hash_chain: true
  redact_paths: false
```

---

# 66. Capability negotiation

At startup produce:

```json
{
  "kernel": "6.x.y",
  "btf": true,
  "ringbuf": true,
  "bpf_lsm": true,
  "bpf_loop": true,
  "send_signal": true,
  "in_kernel_entropy": "enabled",
  "mode": "monitor"
}
```

If something is unavailable:

```text
do not crash
do not silently pretend it exists
report degraded capability
```

---

# 67. Fallback ladder

## Full

```text
vfs_write entropy
+
BPF LSM behavior
+
BPF LSM enforcement
+
canaries
```

## Reduced

```text
vfs_write entropy
+
behavior events
+
agent enforcement
```

## Detection-only

```text
kernel telemetry
+
agent scoring
```

## Sampling fallback

```text
kernel copies bounded sample
+
userspace entropy
+
kernel behavioral enforcement
```

This keeps the project useful even when one advanced capability is missing.

---

# 68. `Makefile` skeleton

```make
CLANG ?= clang
BPFTOOL ?= bpftool

CFLAGS := -O2 -g -Wall -Wextra
BPF_CFLAGS := $(CFLAGS) -target bpf

all: bpf agent

vmlinux.h:
	mkdir -p bpf
	$(BPFTOOL) btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h

bpf: vmlinux.h
	$(CLANG) $(BPF_CFLAGS) -c bpf/p2_fs.bpf.c -o build/p2_fs.bpf.o
	$(CLANG) $(BPF_CFLAGS) -c bpf/p2_lsm.bpf.c -o build/p2_lsm.bpf.o

agent:
	$(CC) $(CFLAGS) agent/main.c -lbpf -lelf -lz -o build/aegisd

test:
	pytest -q

clean:
	rm -rf build
```

This is a scaffold. Match include paths and installed libbpf versions on your environment.

---

# 69. Build order

Do not implement everything at once.

## Phase 1

```text
environment probe
    |
    v
hello-world vfs_write
    |
    v
ring buffer
```

## Phase 2

```text
Python entropy reference
    |
    v
C entropy reference
    |
    v
lookup table
```

## Phase 3

```text
BPF histogram
    |
    v
fixed-point entropy
```

## Phase 4

```text
LSM hooks
    |
    v
canary detection
```

## Phase 5

```text
proc_state
    |
    v
risk decay
    |
    v
evidence fusion
```

## Phase 6

```text
SIGKILL
    +
LSM deny
```

## Phase 7

```text
measurement
    |
    v
false-positive tuning
```

Only after these are stable should you integrate the other Aegis pillars.

---

# 70. Unit testing strategy

Pure functions should be tested outside BPF.

Test:

```text
entropy
Miller–Madow correction
risk decay
evidence weighting
tier calculation
sampling decision
rate buckets
file extension classifier
```

Example:

```text
input
    uniform histogram

expected
    entropy ≈ known reference

result
    exact/within predefined tolerance
```

---

# 71. Differential testing

Every important mathematical operation should have:

```text
Python reference
C implementation
BPF-compatible implementation
```

For each test vector:

```text
same input
    |
    +--> Python
    +--> C
    +--> BPF harness
```

Assert:

```text
abs(reference - implementation) <= tolerance
```

For quantized logic, strive for:

```text
bit-exact
```

---

# 72. Adversarial entropy test vectors

Test:

```text
all zeroes
all 0xFF
alternating 0x00 / 0xFF
ASCII text
UTF-8 text
source code
JPEG
PNG
ZIP
random bytes
encrypted copies
short samples
sparse data
repeated patterns
```

This detects threshold mistakes early.

---

# 73. Threshold calibration

Procedure:

```text
1. collect benign data
2. compute distributions
3. choose maximum allowed FPR
4. evaluate recall under that bound
5. freeze thresholds
6. run held-out test set
```

Never do:

```text
look at final test result
change threshold
look again
```

That creates test-set leakage.

---

# 74. Evaluation metrics

Report:

## Detection

```text
TPR
FPR
precision
recall
F1
ROC-AUC
PR-AUC
```

## Speed

```text
detection latency
block latency
```

## Damage

```text
files lost before block
bytes lost before block
```

## Cost

```text
CPU %
RSS
map memory
I/O throughput
p99 write latency
```

## Reliability

```text
ring-buffer drops
sample-copy failure rate
map evictions
```

## Safety

```text
false kills / 72 h
never-kill violations
```

---

# 75. Main experiments

| ID | Question |
|---|---|
| E2 | Does multi-signal P2 outperform entropy-only? |
| E4 | Is false-positive rate acceptable in normal use? |
| E8 | Which evasion-style workload patterns break coverage? |
| E9 | Can the protection itself be tampered with? |
| E10 | What is the runtime overhead? |
| E11 | Which kernel versions load correctly? |
| E12 | Does failure injection preserve fail-open behavior? |

The original Aegis evaluation plan also includes E1/E3/E5/E6/E7 for other pillars/cross-layer work.

---

# 76. Statistical rigor

Use at least:

```text
10 repeated runs per configuration
```

with different random seeds.

Report:

```text
mean
standard deviation
95% confidence interval
```

For paired ablations:

```text
same workload seed
```

across configurations.

Possible tests:

```text
paired t-test
Wilcoxon signed-rank
```

Choose based on the distribution and state the choice.

---

# 77. Cross-layer ablation

The larger Aegis thesis depends on adaptive sensing.

For the ransomware layer, isolate:

```text
A:
fixed-rate sampling

B:
adaptive sampling

C:
adaptive without HID-taint

D:
adaptive without PMU
```

Measure:

```text
CPU overhead
detection latency
files lost
```

Do not claim the cross-layer mechanism helps unless the ablation demonstrates it.

---

# 78. Coverage gaps

## `mmap(MAP_SHARED)`

A content write can reach the filesystem through page-cache writeback rather than the `vfs_write` entry.

Countermeasures:

```text
canaries
rename/unlink/truncate hooks
write-open behavior
rate/breadth
mmap-related behavioral hooks where verified
```

## `io_uring`

Some I/O may not enter the exact `vfs_write` hook you selected.

Countermeasures:

```text
LSM behavior
canaries
rate
breadth
future iter-write coverage
```

## vectored/copy paths

Examples:

```text
writev
pwritev
sendfile
copy_file_range
```

Add compatible hooks later or rely on behavioral signals.

---

# 79. False-positive hazards

High-risk benign patterns include:

```text
compiler builds
large backups
photo imports
archive creation
video encoding
database vacuum/compaction
package managers
git operations
compression-heavy workloads
```

Do not make a rule like:

```text
"100 high-entropy writes = ransomware"
```

without checking context.

---

# 80. Safety test suite

Write explicit tests for:

```text
PID 1
kernel thread
aegisd itself
aegisd child
ring buffer full
map lookup failure
policy invalid
policy missing
sample copy failure
entropy table missing
risk state missing
kill rate exceeded
agent crashed
LSM unavailable
```

Expected result should be documented for every case.

---

# 81. Failure injection

Example scenarios:

## Ring buffer full

Expected:

```text
drop event
increment counter
continue safely
```

## Map full

Expected:

```text
lookup miss / update miss
increment counter
allow
```

## Corrupted policy

Expected:

```text
reject policy
keep last known-safe policy
do not activate unknown enforcement
```

## Agent crash

Expected:

```text
kernel must remain stable
state is observable after restart
no uncontrolled kill storm
```

## Entropy table missing

Expected:

```text
disable content-sampling branch
continue behavioral detection
report degraded mode
```

---

# 82. Logging format

Use JSON Lines:

```text
{"ts":"...","event":"FS_WRITE","pid":123,"ino":55,"bytes":4096}
{"ts":"...","event":"HIGH_ENTROPY","pid":123,"entropy_q16":521000}
{"ts":"...","event":"CANARY_HIT","pid":123,"ino":99}
{"ts":"...","event":"KILL_DECISION","pid":123,"risk_q8":21500}
```

Do not log raw file contents.

---

# 83. Health counters

Keep counters such as:

```text
sample_attempts
sample_success
sample_copy_fail
entropy_events
canary_hits
rename_events
unlink_events
ringbuf_reserve_fail
risk_updates
kills_attempted
kills_blocked_by_never_kill
kills_rate_limited
lsm_denies
map_misses
map_update_fail
```

Expose them in:

```bash
aegisctl status
```

---

# 84. Debugging commands

## Program list

```bash
sudo bpftool prog show
```

## Map list

```bash
sudo bpftool map show
```

## Link list

```bash
sudo bpftool link show
```

## BPF logs

```bash
sudo cat /sys/kernel/debug/tracing/trace_pipe
```

Use this only for debugging and keep production event delivery on the ring buffer.

## Inspect BTF

```bash
sudo bpftool btf dump file /sys/kernel/btf/vmlinux format c \
  | less
```

---

# 85. Measuring BPF complexity

Record:

```text
verifier processed instruction count
program run time
map memory
event rate
```

Use:

```bash
bpftool prog profile
```

where supported, or collect runtime statistics from the installed kernel/tooling.

This is important because a 4 KiB entropy loop is materially more expensive than a simple metadata hook.

---

# 86. Performance budget

Recommended project target from the source plan:

```text
< 3% average CPU
< 5% fio throughput regression
< 100 MB agent RSS
```

These are targets, not guarantees.

Measure:

```text
Aegis off
Aegis monitor
Aegis alert
Aegis enforce
```

separately.

---

# 87. Benchmark table

Create a table such as:

| Configuration | CPU % | fio MB/s | p99 latency | Detection ms | Files lost |
|---|---:|---:|---:|---:|---:|
| Aegis off | | | | N/A | N/A |
| Monitor, fixed | | | | | |
| Monitor, adaptive | | | | | |
| Enforce, fused | | | | | |

Do not fill with invented numbers.

---

# 88. Review/demo sequence

A five-minute demonstration can be:

```text
1. boot clean VM
2. aegisctl status
3. show monitor mode
4. run benign compile/compression workload
5. show risk stays low
6. run safe encryptor-like benchmark on synthetic corpus
7. show high-entropy events
8. touch synthetic canary
9. show CANARY_HIT
10. show score crossing threshold
11. show would_kill in monitor mode
12. switch to enforce
13. repeat
14. show process termination
15. show later writes returning EPERM
16. print files-lost-before-block
17. show incident JSON
18. reset VM snapshot
```

---

# 89. What to say when a feature fails

Bad:

> “The detector handles everything.”

Good:

> “The content sensor covers the observed write path. `mmap` and `io_uring` require behavioral coverage and are explicitly evaluated as coverage gaps.”

Bad:

> “Zero files can be changed.”

Good:

> “The first write can race detection; therefore we measure files modified before enforcement becomes effective.”

---

# 90. From-scratch implementation checklist

## Day 1

```text
[ ] VM snapshot
[ ] kernel probe
[ ] BTF confirmed
[ ] BPF LSM status known
[ ] bpftool status
[ ] clang/libbpf toolchain
[ ] repository initialized
```

## Day 2

```text
[ ] vfs_write fentry program
[ ] ringbuf
[ ] user-space consumer
[ ] event visible
```

## Day 3

```text
[ ] Python entropy reference
[ ] C entropy reference
[ ] test vectors
[ ] lookup-table generator
```

## Day 4

```text
[ ] BPF scratch map
[ ] histogram
[ ] bpf_loop spike
[ ] entropy result
```

## Day 5

```text
[ ] LSM hook
[ ] canary creation
[ ] canary map
[ ] CANARY_HIT
```

## Day 6

```text
[ ] proc_state
[ ] fixed-point risk
[ ] evidence weights
[ ] decay
[ ] tiering
```

## Day 7

```text
[ ] monitor mode
[ ] would_kill
[ ] never-kill
[ ] kill rate limiter
```

## Day 8

```text
[ ] SIGKILL
[ ] LSM deny
[ ] measured block latency
[ ] cgroup cleanup
```

## Day 9

```text
[ ] corpus generator
[ ] safe encryptor-like workloads
[ ] benign workload suite
```

## Day 10

```text
[ ] E2
[ ] E4
[ ] E8
[ ] E10
[ ] graphs
[ ] review demo
```

---

# 91. Minimal command workflow

```bash
# 1. create workspace
mkdir -p ~/aegis
cd ~/aegis

# 2. create/build vmlinux.h
bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h

# 3. build entropy table
python3 tools/build_entropy_table.py

# 4. build
make

# 5. start in monitor mode
sudo ./build/aegisd --config config/aegis.yaml

# 6. inspect health
sudo ./aegisctl status

# 7. generate synthetic data
python3 tools/make_corpus.py

# 8. run benign workload
./tools/run_benign_suite.sh

# 9. run safe encryptor-like benchmark
./tools/run_safe_encryptor_like.sh

# 10. collect results
python3 eval/run.py --config eval/protocol.md
```

Replace scripts with your actual implementation paths.

---

# 92. Suggested C abstractions

Keep the implementation modular.

```text
risk.h
    decay
    add_evidence
    tier_from_risk

entropy.h
    histogram
    entropy_q16
    Miller–Madow

policy.h
    thresholds
    mode
    safe-path decision

identity.h
    exe key
    trust lookup

sampling.h
    rate decision

safety.h
    never-kill
    rate limit
```

This makes them unit-testable.

---

# 93. Avoid this anti-pattern

Do not put everything in one BPF file:

```text
p2_fs.bpf.c
    2,000 lines
    entropy
    policy
    logging
    canaries
    risk
    kill
```

Prefer:

```text
common.h
entropy.bpf.h
risk.bpf.h
policy.h
p2_fs.bpf.c
p2_lsm.bpf.c
```

so shared logic is explicit.

---

# 94. Avoid threshold magic numbers

Bad:

```c
if (entropy_q16 > 520000)
    kill();
```

Better:

```c
__u32 threshold = policy_entropy_threshold(
    sample_n,
    file_class,
    ps->tier
);

if (entropy_q16 > threshold)
    add_entropy_evidence(ps);
```

Then policy changes do not require recompiling the program.

---

# 95. State machine

Recommended process state:

```text
             +--------------------+
             |                    |
             v                    |
         OBSERVE <--- decay -----+
             |
             | evidence
             v
        HEIGHTENED
             |
             | more evidence
             v
         RESTRICT
             |
             | strong evidence
             v
         QUARANTINED
             |
             +--> SIGKILL
             |
             +--> LSM DENY
```

Recovery:

```text
QUARANTINED
    |
    +--> remains until explicit cleanup
```

Do not automatically “unquarantine” a process after a few milliseconds.

---

# 96. Evidence provenance

Every risk contribution should be traceable.

For example:

```json
{
  "type": "HIGH_ENTROPY",
  "pid": 1234,
  "weight": 2,
  "sample_bytes": 4096,
  "entropy_q16": 521093,
  "timestamp_ns": 123456789
}
```

At decision time:

```json
{
  "risk_before": 17300,
  "evidence": [
    "HIGH_ENTROPY",
    "EXT_CHURN",
    "CANARY_HIT"
  ],
  "risk_after": 22100,
  "tier": 3
}
```

This is critical for debugging false positives.

---

# 97. Explainability requirement

The agent should be able to answer:

```text
Why did this PID become high risk?
```

Example:

```text
PID 1234
risk: 84.0

Evidence:
  +40 canary hit
  +12 extension churn
  +10 high file breadth across 2 windows
  +8 entropy jump
  +15 taint/context multiplier

Action:
  tier 3
  SIGKILL
  future writes denied
```

Avoid opaque:

```text
score = 83
```

with no explanation.

---

# 98. Reproducibility metadata

Every result file should include:

```json
{
  "git_commit": "...",
  "kernel": "...",
  "cpu": "...",
  "vm": true,
  "seed": 1337,
  "corpus_hash": "...",
  "policy_hash": "...",
  "entropy_table_hash": "...",
  "mode": "monitor",
  "sample_bytes": 4096
}
```

This turns a demo into an experiment.

---

# 99. Held-out evaluation

Use:

```text
train/calibration
validation
test
surprise/held-out
```

Do not tune on:

```text
test
surprise
```

Example split:

```text
Run 1–6:
    calibration

Run 7–8:
    validation

Run 9–10:
    test

new workload family:
    surprise
```

---

# 100. Evasion-style benchmark matrix

You should not claim universal coverage. Explicitly evaluate:

| Pattern | Primary coverage | Expected weakness |
|---|---|---|
| high-rate full-file transform | entropy + rate + canary | low |
| partial transform | entropy delta + header + canary | medium |
| low-and-slow | decay windows + canary | medium |
| new-file then unlink | new file entropy + unlink pattern | medium |
| heavy compression | context + file class | false-positive risk |
| `mmap` write | behavior + canary | content visibility gap |
| `io_uring` | behavior + canary | content visibility gap |
| trusted binary abused | canary + drift | allow-list risk |
| single-file change | content only | low confidence |
| database maintenance | file class + benign baseline | false-positive risk |

---

# 101. Why the canary is so important

Suppose:

```text
process modifies:
  100 ordinary files
```

Entropy may be:

```text
ambiguous
```

Suppose instead:

```text
process modifies:
  5 ordinary files
  1 canary
```

Aegis gets a strong semantic clue:

```text
a deliberately protected file was touched
```

Therefore a single canary hit can justify a significant risk jump.

---

# 102. Why the risk engine should decay

Without decay:

```text
one benign event today
+
another benign event next week
=
permanent high risk
```

With decay:

```text
old evidence fades
new evidence dominates
```

This makes normal workflows recover toward baseline.

Canary and backup-tamper evidence may reasonably receive longer-lived effects than ephemeral rate spikes.

---

# 103. Sampling and overhead relationship

Approximate relationship:

```text
more sampling
    -> more CPU
    -> lower detection latency
```

Therefore the optimization problem is:

```text
minimize overhead
subject to acceptable detection latency and files lost
```

The cross-layer controller attempts to solve this dynamically.

---

# 104. P2-only implementation boundary

For a 25% review, keep out:

```text
PMU
HID
Random Forest
dashboard
self-protection
full magic-number classification
```

Keep in:

```text
P2 entropy
P2 canaries
P2 behavior hooks
risk engine
enforcement
safety
measurement
```

This preserves a coherent vertical slice.

---

# 105. Acceptance tests

## Test A — basic telemetry

```text
action:
    append 1 KB to synthetic file

expect:
    FS_WRITE event
```

## Test B — entropy reference

```text
action:
    process known random buffer

expect:
    Python ≈ C reference
```

## Test C — BPF entropy

```text
action:
    safe benchmark writes random-looking transformed buffers

expect:
    high-entropy evidence
```

## Test D — canary

```text
action:
    benchmark modifies canary

expect:
    CANARY_HIT
```

## Test E — risk escalation

```text
action:
    entropy + rename + breadth + canary

expect:
    tier >= kill threshold
```

## Test F — monitor mode

```text
expect:
    would_kill
    process remains alive
```

## Test G — enforce mode

```text
expect:
    SIGKILL
    later writes denied
```

## Test H — never kill

```text
action:
    inject synthetic evidence into protected PID fixture

expect:
    no kill
    safety counter increments
```

---

# 106. Troubleshooting guide

## Verifier rejects program

Try:

```text
1. smaller sample
2. bpf_loop
3. split helper functions
4. simplify pointer arithmetic
5. move scratch to PERCPU map
6. reduce local stack usage
```

Do not blindly add complexity until the verifier accepts it.

## Ring buffer has drops

Check:

```text
event size
event rate
ring buffer size
consumer speed
```

Also reduce event frequency.

Emit:

```text
interesting transitions
```

instead of:

```text
every low-value operation
```

## Entropy threshold looks wrong

Check:

```text
sample size
finite-sample bias
Miller–Madow correction
file class
histogram correctness
Q16 scaling
integer overflow
```

## Too many false positives

Inspect:

```text
compression
archives
photo imports
compilers
databases
backups
trusted executables
```

Do not immediately increase the threshold globally.

Instead ask:

```text
Which evidence type is causing the error?
```

---

# 107. Common implementation mistakes

## Mistake 1

Computing entropy on every write.

**Fix:** gate and sample.

## Mistake 2

Putting a 256-entry histogram on the BPF stack.

**Fix:** per-CPU map.

## Mistake 3

Using floating point in BPF.

**Fix:** fixed-point lookup table.

## Mistake 4

Killing on entropy alone.

**Fix:** evidence fusion.

## Mistake 5

Trusting executable names.

**Fix:** executable identity.

## Mistake 6

Using path as canary identity.

**Fix:** `(dev, inode, generation)`.

## Mistake 7

Assuming LSM sees write bytes.

**Fix:** content sensor + enforcement split.

## Mistake 8

Claiming the first write is blocked.

**Fix:** report files lost before block.

## Mistake 9

Testing on real files.

**Fix:** disposable VM + synthetic corpus.

## Mistake 10

Tuning on the test set.

**Fix:** held-out test + surprise workload.

---

# 108. Suggested file-by-file implementation order

```text
bpf/events.h
bpf/maps.h
        |
        v
bpf/p2_fs.bpf.c
        |
        v
agent/events.c
        |
        v
tools/build_entropy_table.py
        |
        v
bpf/entropy.bpf.h
        |
        v
bpf/p2_lsm.bpf.c
        |
        v
agent/canary.c
        |
        v
bpf/risk.bpf.h
        |
        v
agent/policy.c
        |
        v
agent/enforce.c
        |
        v
tools/make_corpus.py
        |
        v
evaluation harness
```

---

# 109. Minimal source tree for the first working build

Before trying to build the whole project, get this tiny tree working:

```text
aegis/
├── bpf/
│   ├── vmlinux.h
│   ├── events.h
│   ├── maps.h
│   └── p2_fs.bpf.c
├── agent/
│   ├── main.c
│   └── events.c
├── tools/
│   └── build_entropy_table.py
└── Makefile
```

Once that runs:

```text
add entropy
```

then:

```text
add LSM
```

then:

```text
add risk
```

then:

```text
add enforcement
```

---

# 110. Final implementation architecture

At completion, the ransomware layer should look like:

```text
                         +-------------------------+
                         |        POLICY            |
                         | thresholds / modes /     |
                         | safe lists / sampling    |
                         +------------+-------------+
                                      |
                                      v
                        +--------------------------+
                        |      SHARED BPF MAPS      |
                        |                           |
                        | proc_state                |
                        | canary_set                |
                        | trusted_exe               |
                        | file_class                |
                        | nlog2n_tab                |
                        | counters                  |
                        | events                    |
                        +-------------+-------------+
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
                 v                    v                    v
          +-------------+      +-------------+      +-------------+
          | vfs_write   |      | BPF LSM     |      | process     |
          | content     |      | behavior +  |      | context     |
          | entropy     |      | enforcement |      | / lineage   |
          +------+------+      +------+------+      +------+------+
                 |                    |                    |
                 +--------------------+--------------------+
                                      |
                                      v
                              +---------------+
                              | risk engine   |
                              +-------+-------+
                                      |
                    +-----------------+----------------+
                    |                 |                |
                    v                 v                v
                observe           restrict           kill
                    |                 |                |
                    +-----------------+----------------+
                                      |
                                      v
                            quarantine + evidence
                                      |
                                      v
                                  `aegisd`
                                      |
                 +--------------------+-------------------+
                 |                    |                   |
                 v                    v                   v
             cgroup.kill          forensics          incident JSON
```

---

# 111. The exact execution sequence to implement

This is the implementation spine to memorize:

```text
1. file operation enters kernel

2. check whether the file/process qualifies for monitoring

3. apply cheap sampling gate

4. if sampled:
       copy bounded user buffer
       build 256-bin histogram
       compute Q16 entropy
       apply finite-sample correction

5. update file/process behavioral counters

6. look for:
       entropy high
       entropy jump
       header change
       rename churn
       unlink burst
       breadth increase
       canary touch
       backup tamper
       process context

7. decay old risk

8. add new evidence

9. recompute tier

10. if monitor:
       emit would_* event

11. if restrict:
       LSM denies unsafe writes

12. if kill threshold crossed:
       mark QUARANTINED
       emit KILL_DECISION
       bpf_send_signal(SIGKILL)

13. LSM blocks racing/subsequent writes

14. aegisd receives event

15. aegisd contains the process tree

16. collect forensic metadata

17. create incident record

18. record:
       detection latency
       block latency
       files lost
       bytes lost
       overhead

19. reset VM and repeat with controlled seed
```

---

# 112. What the final report should contain

## Section A — Architecture

```text
kernel hooks
maps
agent
trust boundaries
```

## Section B — Entropy

```text
math
fixed-point representation
finite-sample correction
verifier constraints
reference parity
```

## Section C — Behavior

```text
canaries
rate
rename/unlink
file classes
```

## Section D — Enforcement

```text
monitor
alert
restrict
kill
LSM deny
safety
```

## Section E — Results

```text
files lost
latency
false positives
overhead
kernel complexity
```

## Section F — Limits

```text
mmap
io_uring
trusted executables
compressed data
VM effects
kernel-version dependence
```

---

# 113. Final “do not claim” list

Do not claim:

```text
"detects all ransomware"
```

Do not claim:

```text
"blocks the first malicious write"
```

Do not claim:

```text
"entropy uniquely identifies encryption"
```

Do not claim:

```text
"works identically on every kernel"
```

Do not claim:

```text
"zero overhead"
```

Do not claim:

```text
"zero false positives"
```

Instead report the measured values and limits.

---

# 114. Project-specific source alignment

This document expands the ransomware portion of the Aegis master plan:

```text
Pillar 2:
    entropy + behavior + canaries

N3:
    verifier-safe fixed-point entropy

N5:
    multi-view ransomware evidence fusion

N6:
    canary placement/optimization

N1:
    risk-adaptive sensing

Section 10:
    shared per-process risk state

Section 11:
    detect-then-deny + safety

Section 14:
    evaluation

Section 15:
    safe workload generation
```

The source review slice prioritizes exactly this vertical slice before PMU, HID, dashboard, ML, and self-protection are attempted.

---

# 115. Final acceptance checklist

```text
FOUNDATION
[ ] disposable VM
[ ] BTF
[ ] BPF LSM status
[ ] ring buffer
[ ] capability report

TELEMETRY
[ ] vfs_write events
[ ] LSM events
[ ] process identity
[ ] counters

ENTROPY
[ ] Python reference
[ ] C reference
[ ] Q16 table
[ ] Miller–Madow
[ ] sample-size thresholds
[ ] differential tests
[ ] copy-failure measurement
[ ] verifier result

BEHAVIOR
[ ] canary manager
[ ] canary map
[ ] rename
[ ] unlink
[ ] breadth
[ ] backup watch
[ ] file-class state

RISK
[ ] proc_state
[ ] decay
[ ] evidence weights
[ ] multipliers
[ ] tiers
[ ] explanation

ENFORCEMENT
[ ] monitor
[ ] alert
[ ] restrict
[ ] quarantine
[ ] SIGKILL
[ ] LSM EPERM
[ ] cgroup containment

SAFETY
[ ] PID 1 protected
[ ] kernel threads protected
[ ] aegisd protected
[ ] rate limit
[ ] kill-switch
[ ] fail-open
[ ] dry-run

EVALUATION
[ ] synthetic corpus
[ ] benign workloads
[ ] safe encryptor-like workloads
[ ] E2
[ ] E4
[ ] E8
[ ] E10
[ ] held-out test set
[ ] confidence intervals
[ ] files-lost metric
[ ] overhead metric

DOCUMENTATION
[ ] incident schema
[ ] capability matrix
[ ] limitations
[ ] reproducibility metadata
[ ] recorded demo
```

---

# 116. Bottom line

The ransomware execution layer is not one BPF program.

It is a controlled pipeline:

```text
filesystem events
      ↓
bounded content sampling
      ↓
behavioral evidence
      ↓
canary evidence
      ↓
per-process decayed risk
      ↓
tiered decision
      ↓
detect-then-deny
      ↓
safe containment
      ↓
forensics + measurement
```

The engineering objective is to make every step:

```text
bounded
measurable
explainable
fail-open
reproducible
```

The scientific objective is to prove, with controlled experiments, whether the fused design reduces:

```text
detection latency
files lost before block
CPU overhead
false positives
```

without turning the detector itself into an unsafe component.
