#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define __BPF__ 1
#include "common.h"

char LICENSE[] SEC("license") = "GPL";

/* 1. Ring Buffer for Telemetry Events */
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 2 * 1024 * 1024); /* 2MB Buffer */
} events SEC(".maps");

/* 2. Process Behavioral Risk State */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 8192);
    __type(key, __u32);                 /* TGID */
    __type(value, struct proc_state);
} proc_state_map SEC(".maps");

/* 3. Decoy Canary Registry */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, struct devino_key);
    __type(value, __u8);
} canary_set SEC(".maps");

/* 4. Magic Number File-Class Cache */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 65536);
    __type(key, struct devino_key);
    __type(value, __u8);                /* 0=Unknown, 1=Text, 2=Compressed, 3=Media */
} magic_cache SEC(".maps");

/* 5. Precomputed nlog2n Q16.16 Table */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 4097);
    __type(key, __u32);                 /* 0..4096 */
    __type(value, __u32);               /* Q16.16 fixed-point */
} nlog2n_tab SEC(".maps");

/* 6. Per-CPU Scratch Space */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct entropy_scratch);
} scratch_map SEC(".maps");

/* 7. Allowlisted System Executables */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, struct devino_key);
    __type(value, __u8);
} trusted_exe SEC(".maps");

/* 8. Never-Kill Process Whitelist */
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 64);
    __type(key, __u32);                 /* TGID */
    __type(value, __u8);
} never_kill_pids SEC(".maps");

/* 9. Global Operational Configuration */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 16);
    __type(key, __u32);
    __type(value, __u32);
} policy_cfg SEC(".maps");

/* 10. System Health & Performance Counters */
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, MAX_COUNTERS);
    __type(key, __u32);
    __type(value, __u64);
} counters SEC(".maps");

/* 11. Enforcement Rate-Limiting Sliding Window */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, __u64[2]);            /* [window_start_ns, kill_count] */
} kill_rate SEC(".maps");

#include "lib/entropy.h"
#include "lib/risk.h"

#define S_ISREG_BITS 0170000
#define S_IFREG_VAL  0100000
#define MAY_WRITE    0x00000002

static __always_inline void bump_counter(__u32 id)
{
    __u32 key = id;
    __u64 *val = bpf_map_lookup_elem(&counters, &key);
    if (val)
        (*val)++;
}

static __always_inline int is_never_kill(__u32 tgid)
{
    if (tgid <= 1)
        return 1;
    struct task_struct *task = (struct task_struct *)bpf_get_current_task();
    if (BPF_CORE_READ(task, flags) & PF_KTHREAD)
        return 1;
    __u8 *exempt = bpf_map_lookup_elem(&never_kill_pids, &tgid);
    return exempt != NULL;
}

static __always_inline void emit_ringbuf_event(
    __u8 type,
    __u32 tgid,
    __u32 pid,
    __u64 ino,
    __u32 dev,
    __u32 count,
    __u32 entropy_q16,
    __u32 risk_q8,
    __u8 tier)
{
    struct fs_event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return;

    e->ts_ns = bpf_ktime_get_ns();
    e->type = type;
    e->tgid = tgid;
    e->pid = pid;
    e->ino = ino;
    e->dev = dev;
    e->count = count;
    e->entropy_q16 = entropy_q16;
    e->risk_q8 = risk_q8;
    e->tier = tier;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
}

SEC("fentry/vfs_write")
int BPF_PROG(on_vfs_write, struct file *file, const char *buf, size_t count, loff_t *pos)
{
    bump_counter(COUNTER_TOTAL_WRITES);

    struct inode *inode = BPF_CORE_READ(file, f_inode);
    if (!inode)
        return 0;

    umode_t mode = BPF_CORE_READ(inode, i_mode);
    if ((mode & S_ISREG_BITS) != S_IFREG_VAL)
        return 0; /* Ignore sockets, pipes, special files */

    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 tgid = pid_tgid >> 32;
    __u32 pid = (__u32)pid_tgid;

    /* Exempt protected processes immediately */
    if (is_never_kill(tgid))
        return 0;

    __u64 ino = BPF_CORE_READ(inode, i_ino);
    __u32 dev = BPF_CORE_READ(inode, i_sb, s_dev);
    struct devino_key fkey = { .dev = dev, .ino = ino };

    /* 1. Fast Path: Decoy Canary Breach Detection */
    __u8 *is_canary = bpf_map_lookup_elem(&canary_set, &fkey);
    struct proc_state *ps = bpf_map_lookup_elem(&proc_state_map, &tgid);

    if (is_canary) {
        bump_counter(COUNTER_CANARY_HIT);
        if (!ps) {
            struct proc_state new_ps = {0};
            new_ps.last_update_ns = bpf_ktime_get_ns();
            new_ps.flags = FLAG_CANARY_HIT;
            new_ps.risk_q8 = apply_evidence_q8(0, 40 << 8, 256);
            new_ps.tier = evaluate_tier(new_ps.risk_q8);
            bpf_map_update_elem(&proc_state_map, &tgid, &new_ps, BPF_ANY);
            ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
        } else {
            ps->flags |= FLAG_CANARY_HIT;
            ps->risk_q8 = apply_evidence_q8(ps->risk_q8, 40 << 8, 256);
            ps->tier = evaluate_tier(ps->risk_q8);
        }

        emit_ringbuf_event(EVENT_CANARY_HIT, tgid, pid, ino, dev, count, 0, ps ? ps->risk_q8 : 0, ps ? ps->tier : 0);

        if (ps && ps->tier >= TIER_3_QUARANTINE) {
            ps->flags |= FLAG_QUARANTINED;
            bpf_send_signal(SIGKILL);
            bump_counter(COUNTER_KILL_DECISION);
            emit_ringbuf_event(EVENT_KILL_DECISION, tgid, pid, ino, dev, count, 0, ps->risk_q8, ps->tier);
        }
        return 0;
    }

    /* 2. Skip Content Inspection if already Quarantined or Sub-Threshold */
    if (ps && (ps->flags & FLAG_QUARANTINED)) {
        return 0;
    }
    if (count < MIN_SAMPLE_BYTES) {
        return 0;
    }

    /* 3. Adaptive Sampling Gate */
    if (ps && ps->sample_shift > 0) {
        __u64 now = bpf_ktime_get_ns();
        if ((now & ((1 << ps->sample_shift) - 1)) != 0)
            return 0;
    }

    /* 4. Verifier-Safe In-Kernel Entropy Measurement */
    __u32 entropy_q16 = 0;
    __u32 kobs = 0;
    int ret = compute_kernel_entropy_q16(buf, count, &entropy_q16, &kobs);
    if (ret != 0) {
        if (ret == -2)
            bump_counter(COUNTER_ENTROPY_READ_FAIL);
        return 0; /* Fail open */
    }

    /* 5. State Machine Update & Decay */
    __u64 now = bpf_ktime_get_ns();
    if (!ps) {
        struct proc_state initial_ps = {0};
        initial_ps.last_update_ns = now;
        initial_ps.sample_shift = 4; /* Default 1-in-16 */
        bpf_map_update_elem(&proc_state_map, &tgid, &initial_ps, BPF_ANY);
        ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
        if (!ps)
            return 0;
    }

    __u64 elapsed_ms = (now - ps->last_update_ns) / 1000000ULL;
    ps->risk_q8 = decay_risk_q8(ps->risk_q8, elapsed_ms);
    ps->last_update_ns = now;

    /* Threshold check: 7.8 bits = 511180 in Q16.16 */
    if (entropy_q16 >= 511180) {
        ps->flags |= FLAG_HI_ENTROPY;
        ps->risk_q8 = apply_evidence_q8(ps->risk_q8, 2 << 8, 256);
        emit_ringbuf_event(EVENT_WRITE_SAMPLE, tgid, pid, ino, dev, count, entropy_q16, ps->risk_q8, ps->tier);
    }

    __u8 new_tier = evaluate_tier(ps->risk_q8);
    if (new_tier != ps->tier) {
        ps->tier = new_tier;
        emit_ringbuf_event(EVENT_TIER_CHANGE, tgid, pid, ino, dev, count, entropy_q16, ps->risk_q8, ps->tier);
        if (new_tier == TIER_1_SUSPICIOUS) ps->sample_shift = 2; /* 1-in-4 */
        if (new_tier == TIER_2_HOSTILE)    ps->sample_shift = 0; /* 100% */
    }

    /* 6. Enforcement Execution */
    if (ps->tier >= TIER_3_QUARANTINE && !(ps->flags & FLAG_QUARANTINED)) {
        __u32 mode_idx = 0;
        __u32 *mode = bpf_map_lookup_elem(&policy_cfg, &mode_idx);
        __u32 active_mode = mode ? *mode : MODE_MONITOR;

        if (active_mode == MODE_MONITOR) {
            emit_ringbuf_event(EVENT_WOULD_KILL, tgid, pid, ino, dev, count, entropy_q16, ps->risk_q8, ps->tier);
        } else if (active_mode == MODE_ENFORCE) {
            ps->flags |= FLAG_QUARANTINED;
            bpf_send_signal(SIGKILL);
            bump_counter(COUNTER_KILL_DECISION);
            emit_ringbuf_event(EVENT_KILL_DECISION, tgid, pid, ino, dev, count, entropy_q16, ps->risk_q8, ps->tier);
        }
    }

    return 0;
}

SEC("lsm/file_permission")
int BPF_PROG(on_file_permission, struct file *file, int mask)
{
    if (!(mask & MAY_WRITE))
        return 0;

    __u32 tgid = bpf_get_current_pid_tgid() >> 32;
    struct proc_state *ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
    if (ps && (ps->flags & FLAG_QUARANTINED)) {
        ps->total_quarantined_writes++;
        bump_counter(COUNTER_DENIED_WRITE);
        return -1; /* -EPERM */
    }

    return 0;
}

SEC("lsm/inode_rename")
int BPF_PROG(on_inode_rename, struct inode *old_dir, struct dentry *old_dentry,
             struct inode *new_dir, struct dentry *new_dentry)
{
    struct inode *inode = BPF_CORE_READ(old_dentry, d_inode);
    if (!inode)
        return 0;

    __u32 dev = BPF_CORE_READ(inode, i_sb, s_dev);
    __u64 ino = BPF_CORE_READ(inode, i_ino);
    struct devino_key key = { .dev = dev, .ino = ino };

    __u8 *is_canary = bpf_map_lookup_elem(&canary_set, &key);
    if (is_canary) {
        __u64 pid_tgid = bpf_get_current_pid_tgid();
        __u32 tgid = pid_tgid >> 32;
        __u32 pid = (__u32)pid_tgid;

        bump_counter(COUNTER_CANARY_HIT);
        struct proc_state *ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
        if (ps) {
            ps->flags |= FLAG_CANARY_HIT;
            ps->risk_q8 = apply_evidence_q8(ps->risk_q8, 40 << 8, 256);
            ps->tier = evaluate_tier(ps->risk_q8);
            if (ps->tier >= TIER_3_QUARANTINE) {
                ps->flags |= FLAG_QUARANTINED;
                bpf_send_signal(SIGKILL);
                bump_counter(COUNTER_KILL_DECISION);
            }
        }
        emit_ringbuf_event(EVENT_CANARY_HIT, tgid, pid, ino, dev, 0, 0, ps ? ps->risk_q8 : 0, ps ? ps->tier : 0);
    }

    return 0;
}

SEC("lsm/inode_unlink")
int BPF_PROG(on_inode_unlink, struct inode *dir, struct dentry *dentry)
{
    struct inode *inode = BPF_CORE_READ(dentry, d_inode);
    if (!inode)
        return 0;

    __u32 dev = BPF_CORE_READ(inode, i_sb, s_dev);
    __u64 ino = BPF_CORE_READ(inode, i_ino);
    struct devino_key key = { .dev = dev, .ino = ino };

    __u8 *is_canary = bpf_map_lookup_elem(&canary_set, &key);
    if (is_canary) {
        __u64 pid_tgid = bpf_get_current_pid_tgid();
        __u32 tgid = pid_tgid >> 32;
        __u32 pid = (__u32)pid_tgid;

        bump_counter(COUNTER_CANARY_HIT);
        struct proc_state *ps = bpf_map_lookup_elem(&proc_state_map, &tgid);
        if (ps) {
            ps->flags |= FLAG_CANARY_HIT;
            ps->risk_q8 = apply_evidence_q8(ps->risk_q8, 40 << 8, 256);
            ps->tier = evaluate_tier(ps->risk_q8);
            if (ps->tier >= TIER_3_QUARANTINE) {
                ps->flags |= FLAG_QUARANTINED;
                bpf_send_signal(SIGKILL);
                bump_counter(COUNTER_KILL_DECISION);
            }
        }
        emit_ringbuf_event(EVENT_CANARY_HIT, tgid, pid, ino, dev, 0, 0, ps ? ps->risk_q8 : 0, ps ? ps->tier : 0);
    }

    return 0;
}
