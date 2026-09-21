#include "agent.h"
#include <math.h>

#define TABLE_SIZE 4097

int populate_nlog2n_table(int map_fd)
{
    uint32_t key = 0;
    uint32_t val = 0;

    /* Index 0: 0 * log2(0) = 0 */
    if (bpf_map_update_elem(map_fd, &key, &val, BPF_ANY) != 0) {
        perror("Failed to init index 0 of nlog2n table");
        return -1;
    }

    for (uint32_t c = 1; c < TABLE_SIZE; c++) {
        key = c;
        double d_val = (double)c * log2((double)c) * 65536.0;
        val = (uint32_t)(d_val + 0.5); /* Rounding */

        if (bpf_map_update_elem(map_fd, &key, &val, BPF_ANY) != 0) {
            fprintf(stderr, "Failed to update table entry %u: %s\n", c, strerror(errno));
            return -1;
        }
    }
    printf("[+] Successfully populated %d entries in BPF nlog2n_tab\n", TABLE_SIZE);
    return 0;
}
