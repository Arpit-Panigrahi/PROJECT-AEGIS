#include "agent.h"
#include <time.h>

static int handle_event(void *ctx, void *data, size_t data_sz)
{
    const struct fs_event *e = data;
    if (data_sz < sizeof(*e))
        return 0;

    double entropy = (double)e->entropy_q16 / 65536.0;
    double risk = (double)e->risk_q8 / 256.0;

    const char *type_name = "UNKNOWN";
    switch (e->type) {
        case EVENT_WRITE_SAMPLE:  type_name = "WRITE_SAMPLE"; break;
        case EVENT_CANARY_HIT:    type_name = "CANARY_BREACH"; break;
        case EVENT_RENAME_CHURN:  type_name = "RENAME_CHURN"; break;
        case EVENT_UNLINK_CHURN:  type_name = "UNLINK_CHURN"; break;
        case EVENT_NOTE_CREATED:  type_name = "NOTE_CREATED"; break;
        case EVENT_TIER_CHANGE:   type_name = "TIER_CHANGE"; break;
        case EVENT_KILL_DECISION: type_name = "KILL_DECISION"; break;
        case EVENT_WOULD_KILL:    type_name = "WOULD_KILL (MONITOR)"; break;
    }

    /* Print real-time colored log to terminal */
    if (e->type == EVENT_KILL_DECISION) {
        printf("\033[1;31m[!] KILL_DECISION: PID %u (TGID %u, comm: '%s') crossed Tier 3! SIGKILL issued, subsequent writes denied.\033[0m\n",
               e->pid, e->tgid, e->comm);
    } else if (e->type == EVENT_WOULD_KILL) {
        printf("\033[1;33m[!] WOULD_KILL: PID %u (comm: '%s') reached Risk %.1f (Quarantine threshold) in MONITOR mode.\033[0m\n",
               e->pid, e->comm, risk);
    } else if (e->type == EVENT_CANARY_HIT) {
        printf("\033[1;35m[*] CANARY_HIT: PID %u (comm: '%s') touched decoy inode %lu (dev %u). Risk: %.1f, Tier: %u\033[0m\n",
               e->pid, e->comm, (unsigned long)e->ino, e->dev, risk, e->tier);
    } else if (e->type == EVENT_TIER_CHANGE) {
        printf("[*] TIER_CHANGE: PID %u (comm: '%s') transitioned to Tier %u. Risk: %.1f\n",
               e->pid, e->comm, e->tier, risk);
    } else {
        printf("[telemetry] %-14s | PID: %-6u | Comm: %-12s | Count: %-5u | Entropy: %4.2f bits | Risk: %4.1f | Tier: %u\n",
               type_name, e->pid, e->comm, e->count, entropy, risk, e->tier);
    }
    fflush(stdout);

    /* Append JSON line to event logs for frontend real-time consumption */
    FILE *log_fp = fopen("/var/log/aegis/events.jsonl", "a");
    if (!log_fp)
        log_fp = fopen("/tmp/aegis_events.jsonl", "a");
    if (log_fp) {
        fprintf(log_fp,
            "{\"ts\":%llu,\"type\":\"%s\",\"pid\":%u,\"tgid\":%u,\"comm\":\"%s\",\"ino\":%llu,\"dev\":%u,\"count\":%u,\"entropy\":%.2f,\"risk\":%.1f,\"tier\":%u}\n",
            (unsigned long long)e->ts_ns, type_name, e->pid, e->tgid, e->comm,
            (unsigned long long)e->ino, e->dev, e->count, entropy, risk, e->tier);
        fclose(log_fp);
    }
    return 0;
}

int run_event_consumer(struct p2_fs_bpf *skel, volatile sig_atomic_t *stop_flag)
{
    int rb_fd = bpf_map__fd(skel->maps.events);
    if (rb_fd < 0) {
        fprintf(stderr, "[-] Invalid ringbuf map fd\n");
        return -1;
    }

    struct ring_buffer *rb = ring_buffer__new(rb_fd, handle_event, NULL, NULL);
    if (!rb) {
        fprintf(stderr, "[-] Failed to initialize ring buffer\n");
        return -1;
    }

    printf("[+] Ring buffer consumer listening for kernel events...\n");
    while (!(*stop_flag)) {
        int err = ring_buffer__poll(rb, 100 /* ms */);
        if (err < 0 && err != -EINTR) {
            fprintf(stderr, "[-] Error polling ring buffer: %d\n", err);
            break;
        }
    }

    ring_buffer__free(rb);
    return 0;
}
