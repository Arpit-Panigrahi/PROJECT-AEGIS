#ifndef __AEGIS_COMMON_H__
#define __AEGIS_COMMON_H__

#ifdef __BPF__
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#else
#include <linux/types.h>
#endif

#define TASK_COMM_LEN 16
#define SAMPLE_BYTES 4096
#define SAMPLE_MASK (SAMPLE_BYTES - 1)
#define MIN_SAMPLE_BYTES 512

#ifndef PF_KTHREAD
#define PF_KTHREAD 0x00200000
#endif

#ifndef SIGKILL
#define SIGKILL 9
#endif

/* Operational Modes */
#define MODE_MONITOR 0
#define MODE_ALERT   1
#define MODE_ENFORCE 2
#define MODE_LEARN   3

/* Status and Risk Flags */
#define FLAG_CANARY_HIT       (1 << 0)
#define FLAG_HI_ENTROPY       (1 << 1)
#define FLAG_HDR_DESTROYED    (1 << 2)
#define FLAG_EXT_CHURN        (1 << 3)
#define FLAG_NOTE_PATTERN     (1 << 4)
#define FLAG_QUARANTINED      (1 << 5)

/* Event Types for Ring Buffer */
enum event_type {
    EVENT_WRITE_SAMPLE   = 1,
    EVENT_CANARY_HIT     = 2,
    EVENT_RENAME_CHURN   = 3,
    EVENT_UNLINK_CHURN   = 4,
    EVENT_NOTE_CREATED   = 5,
    EVENT_TIER_CHANGE    = 6,
    EVENT_KILL_DECISION  = 7,
    EVENT_WOULD_KILL     = 8
};

/* Telemetry Counter Indices */
enum counter_idx {
    COUNTER_ENTROPY_READ_FAIL = 0,
    COUNTER_DENIED_WRITE      = 1,
    COUNTER_NEVERKILL_SKIP    = 2,
    COUNTER_RATE_LIMITED      = 3,
    COUNTER_CANARY_HIT        = 4,
    COUNTER_KILL_DECISION     = 5,
    COUNTER_MAP_LOOKUP_FAIL   = 6,
    COUNTER_TOTAL_WRITES      = 7,
    MAX_COUNTERS              = 16
};

/* Inode/Device Key */
struct devino_key {
    __u32 dev;
    __u64 ino;
} __attribute__((packed));

/* Per-Process Behavioral & Risk State */
struct proc_state {
    __u64 last_update_ns;
    __u32 risk_q8;               /* Scaled by 256 (0..25600) */
    __u32 files_w_bucket[10];    /* 100ms rolling modification buckets */
    __u32 hi_entropy_bucket[10];
    __u32 rename_bucket[10];
    __u32 unlink_bucket[10];
    __u16 flags;
    __u8  tier;                  /* 0 (Normal), 1 (Suspicious), 2 (Hostile), 3 (Quarantine) */
    __u8  sample_shift;          /* Adaptive sampling shift (0 = 100%, 4 = 1/16th) */
    __u32 total_quarantined_writes;
} __attribute__((aligned(8)));

/* Ring Buffer Event Record */
struct fs_event {
    __u64 ts_ns;
    __u32 pid;
    __u32 tgid;
    __u64 ino;
    __u32 dev;
    __u32 count;
    __u32 entropy_q16;
    __u32 risk_q8;
    __u8  type;
    __u8  tier;
    char  comm[TASK_COMM_LEN];
} __attribute__((aligned(8)));

/* Scratch Memory for In-Kernel Histogram */
struct entropy_scratch {
    __u8  buf[SAMPLE_BYTES];
    __u32 hist[256];
};

#endif /* __AEGIS_COMMON_H__ */
