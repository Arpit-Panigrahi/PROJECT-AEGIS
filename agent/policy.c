#include "agent.h"

int load_policy_config(int policy_map_fd, int mode)
{
    uint32_t key = 0;
    uint32_t val = (uint32_t)mode;

    if (bpf_map_update_elem(policy_map_fd, &key, &val, BPF_ANY) != 0) {
        perror("Failed to update policy mode in policy_cfg map");
        return -1;
    }

    const char *mode_str = "UNKNOWN";
    switch (mode) {
        case MODE_MONITOR: mode_str = "MONITOR (Dry-run telemetry)"; break;
        case MODE_ALERT:   mode_str = "ALERT (Logging alerts only)"; break;
        case MODE_ENFORCE: mode_str = "ENFORCE (Active SIGKILL & LSM -EPERM)"; break;
        case MODE_LEARN:   mode_str = "LEARN (Baseline profiling)"; break;
    }

    printf("[+] Aegis Policy Mode initialized to: %s\n", mode_str);
    return 0;
}
