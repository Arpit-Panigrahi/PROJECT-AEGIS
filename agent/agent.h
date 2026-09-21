#ifndef __AEGIS_AGENT_H__
#define __AEGIS_AGENT_H__

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <signal.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "../bpf/common.h"
#include "p2_fs.skel.h"

/* Prototype declarations */
int populate_nlog2n_table(int map_fd);
int init_canaries(int map_fd, const char *canary_dir);
int load_policy_config(int policy_map_fd, int mode);
int run_event_consumer(struct p2_fs_bpf *skel, volatile sig_atomic_t *stop_flag);

#endif /* __AEGIS_AGENT_H__ */
