#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#define TABLE_SIZE 4097
#define SAMPLE_BYTES 4096

static uint32_t s_nlog2n[TABLE_SIZE];

static void init_table(void)
{
    s_nlog2n[0] = 0;
    for (uint32_t c = 1; c < TABLE_SIZE; c++) {
        double d_val = (double)c * log2((double)c) * 65536.0;
        s_nlog2n[c] = (uint32_t)(d_val + 0.5);
    }
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <length>\n", argv[0]);
        return 1;
    }

    uint32_t n = (uint32_t)atoi(argv[1]);
    if (n > SAMPLE_BYTES) n = SAMPLE_BYTES;

    init_table();

    uint8_t buf[SAMPLE_BYTES];
    size_t read_bytes = fread(buf, 1, n, stdin);
    if (read_bytes < n) {
        fprintf(stderr, "Failed to read requested %u bytes (got %zu)\n", n, read_bytes);
        return 1;
    }

    uint32_t hist[256] = {0};
    for (uint32_t i = 0; i < n; i++) {
        hist[buf[i]]++;
    }

    uint64_t sum_q16 = 0;
    uint32_t k_obs = 0;
    for (uint32_t b = 0; b < 256; b++) {
        if (hist[b] > 0) {
            k_obs++;
            sum_q16 += s_nlog2n[hist[b]];
        }
    }

    uint64_t t_n = s_nlog2n[n];
    if (sum_q16 > t_n) sum_q16 = t_n;

    uint64_t raw_q16 = (t_n - sum_q16) / n;
    if (k_obs > 1) {
        uint64_t bias_q16 = ((uint64_t)(k_obs - 1) * 47274ULL) / n;
        raw_q16 += bias_q16;
    }

    /* Print raw Q16.16 integer value */
    printf("%lu\n", raw_q16);
    return 0;
}
