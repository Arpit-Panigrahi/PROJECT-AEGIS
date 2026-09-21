#ifndef __AEGIS_ENTROPY_H__
#define __AEGIS_ENTROPY_H__

#include "../common.h"

#ifdef __BPF__

struct hist_loop_ctx {
    struct entropy_scratch *scratch;
    __u32 length;
};

static long hist_callback(__u32 index, void *ctx)
{
    struct hist_loop_ctx *hctx = (struct hist_loop_ctx *)ctx;
    if (index >= hctx->length)
        return 1; /* Terminate loop early if reached sample_len */

    __u8 byte_val = hctx->scratch->buf[index & SAMPLE_MASK];
    hctx->scratch->hist[byte_val]++;
    return 0;
}

struct sum_loop_ctx {
    struct entropy_scratch *scratch;
    __u64 sum_q16;
    __u32 k_obs;
};

static long sum_callback(__u32 bin_idx, void *ctx)
{
    struct sum_loop_ctx *sctx = (struct sum_loop_ctx *)ctx;
    if (bin_idx >= 256)
        return 1;

    __u32 count = sctx->scratch->hist[bin_idx & 0xFF];
    if (count > 0) {
        sctx->k_obs++;
        if (count > SAMPLE_BYTES)
            count = SAMPLE_BYTES;

        __u32 key = count;
        __u32 *val = bpf_map_lookup_elem(&nlog2n_tab, &key);
        if (val) {
            sctx->sum_q16 += (__u64)(*val);
        }
    }
    return 0;
}

static __always_inline int compute_kernel_entropy_q16(
    const char *user_buf,
    __u32 count,
    __u32 *out_entropy_q16,
    __u32 *out_kobs)
{
    __u32 zero = 0;
    struct entropy_scratch *scratch = bpf_map_lookup_elem(&scratch_map, &zero);
    if (!scratch)
        return -1;

    __u32 sample_len = count;
    if (sample_len > SAMPLE_BYTES - 1)
        sample_len = SAMPLE_BYTES - 1;
    asm volatile("" : "+r"(sample_len));
    sample_len &= SAMPLE_MASK;
    if (sample_len < MIN_SAMPLE_BYTES)
        return -1;

    /* Safely copy user payload into kernel per-CPU scratch space */
    if (bpf_probe_read_user(scratch->buf, sample_len, user_buf) != 0) {
        return -2; /* Page not resident or invalid pointer */
    }

    /* Zero out histogram array */
    __builtin_memset(scratch->hist, 0, sizeof(scratch->hist));

    /* 1. Build 256-bin histogram */
    struct hist_loop_ctx hctx = { .scratch = scratch, .length = sample_len };
    bpf_loop(SAMPLE_BYTES, hist_callback, &hctx, 0);

    /* 2. Compute Sum(c_i * log2(c_i)) and distinct observed bins (k_obs) */
    struct sum_loop_ctx sctx = { .scratch = scratch, .sum_q16 = 0, .k_obs = 0 };
    bpf_loop(256, sum_callback, &sctx, 0);

    /* 3. Lookup T[N] */
    __u32 key_n = sample_len;
    __u32 *t_n = bpf_map_lookup_elem(&nlog2n_tab, &key_n);
    if (!t_n)
        return -3;

    if (sctx.sum_q16 > (__u64)(*t_n))
        sctx.sum_q16 = (__u64)(*t_n);

    /* Q16.16 Raw Entropy: (T[N] - Sum) / N */
    __u64 raw_entropy_q16 = ((__u64)(*t_n) - sctx.sum_q16) / sample_len;

    /* Miller-Madow Bias Correction: (k_obs - 1) * 47274 / N */
    if (sctx.k_obs > 1) {
        __u64 bias_q16 = ((__u64)(sctx.k_obs - 1) * 47274ULL) / sample_len;
        raw_entropy_q16 += bias_q16;
    }

    *out_entropy_q16 = (__u32)raw_entropy_q16;
    *out_kobs = sctx.k_obs;
    return 0;
}

#endif /* __BPF__ */

#endif /* __AEGIS_ENTROPY_H__ */
