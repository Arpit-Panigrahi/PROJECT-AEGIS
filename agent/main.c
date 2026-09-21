#include "agent.h"

static volatile sig_atomic_t g_stop = 0;

static void sig_handler(int sig)
{
    (void)sig;
    g_stop = 1;
}

static void print_usage(const char *prog)
{
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("Options:\n");
    printf("  -m, --mode <monitor|alert|enforce>  Set operational mode (default: monitor)\n");
    printf("  -c, --canary-dir <dir>              Directory for decoy canaries (default: /tmp/aegis_canaries)\n");
    printf("  -h, --help                          Show this help message\n");
}

int main(int argc, char **argv)
{
    int mode = MODE_MONITOR;
    const char *canary_dir = "/tmp/aegis_canaries";

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-m") == 0 || strcmp(argv[i], "--mode") == 0) {
            if (++i < argc) {
                if (strcmp(argv[i], "monitor") == 0) mode = MODE_MONITOR;
                else if (strcmp(argv[i], "alert") == 0) mode = MODE_ALERT;
                else if (strcmp(argv[i], "enforce") == 0) mode = MODE_ENFORCE;
                else {
                    fprintf(stderr, "Unknown mode: %s\n", argv[i]);
                    return 1;
                }
            }
        } else if (strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--canary-dir") == 0) {
            if (++i < argc) canary_dir = argv[i];
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 0;
        }
    }

    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    printf("===============================================================\n");
    printf("     Project Aegis — Pillar 2: Ransomware Protection Layer    \n");
    printf("===============================================================\n");

    /* 1. Open and load BPF skeleton */
    printf("[*] Loading BPF programs and maps into kernel...\n");
    struct p2_fs_bpf *skel = p2_fs_bpf__open();
    if (!skel) {
        fprintf(stderr, "[-] Failed to open BPF skeleton\n");
        return 1;
    }

    int err = p2_fs_bpf__load(skel);
    if (err) {
        fprintf(stderr, "[-] Failed to load BPF skeleton into kernel: %d\n", err);
        p2_fs_bpf__destroy(skel);
        return 1;
    }
    printf("[+] BPF object verified and loaded successfully.\n");

    /* 2. Populate nlog2n Q16.16 Table */
    int nlog2n_fd = bpf_map__fd(skel->maps.nlog2n_tab);
    if (populate_nlog2n_table(nlog2n_fd) != 0) {
        fprintf(stderr, "[-] Failed to populate nlog2n table\n");
        p2_fs_bpf__destroy(skel);
        return 1;
    }

    /* 3. Initialize and register Decoy Canaries */
    int canary_fd = bpf_map__fd(skel->maps.canary_set);
    if (init_canaries(canary_fd, canary_dir) != 0) {
        fprintf(stderr, "[-] Warning: Some canaries failed to register\n");
    }

    /* 4. Set Initial Policy Mode */
    int policy_fd = bpf_map__fd(skel->maps.policy_cfg);
    if (load_policy_config(policy_fd, mode) != 0) {
        fprintf(stderr, "[-] Failed to set policy config\n");
    }

    /* 5. Attach BPF Hooks */
    printf("[*] Attaching BPF probes (vfs_write + LSM hooks)...\n");
    err = p2_fs_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "[-] Failed to attach BPF skeleton: %d\n", err);
        p2_fs_bpf__destroy(skel);
        return 1;
    }
    printf("[+] All BPF hooks attached and active!\n");

    /* 6. Run Event Loop */
    run_event_consumer(skel, &g_stop);

    /* 7. Clean Shutdown */
    printf("\n[*] Received shutdown signal. Detaching BPF hooks...\n");
    p2_fs_bpf__destroy(skel);
    printf("[+] Project Aegis agent terminated cleanly.\n");

    return 0;
}
