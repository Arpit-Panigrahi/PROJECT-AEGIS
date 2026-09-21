#ifndef __AEGIS_RISK_H__
#define __AEGIS_RISK_H__

#include "../common.h"

#define HALF_LIFE_MS 4000
#define RISK_MAX     (100 << 8)  /* 25600 in Q8 */

#define TIER_0_NORMAL     0
#define TIER_1_SUSPICIOUS 1
#define TIER_2_HOSTILE    2
#define TIER_3_QUARANTINE 3

#define THRESHOLD_TIER1 (25 << 8)
#define THRESHOLD_TIER2 (50 << 8)
#define THRESHOLD_TIER3 (80 << 8)

#ifdef __BPF__
#define RISK_INLINE static __always_inline
#else
#define RISK_INLINE static inline
#endif

RISK_INLINE __u32 decay_risk_q8(__u32 current_risk_q8, __u64 elapsed_ms)
{
    __u32 halvings = (__u32)(elapsed_ms / HALF_LIFE_MS);
    if (halvings >= 16)
        return 0;
    return current_risk_q8 >> halvings;
}

RISK_INLINE __u32 apply_evidence_q8(
    __u32 current_risk_q8,
    __u32 weight_q8,
    __u32 multiplier_q8)
{
    __u64 increment = ((__u64)weight_q8 * (__u64)multiplier_q8) >> 8;
    __u64 total = (__u64)current_risk_q8 + increment;
    return (total > RISK_MAX) ? RISK_MAX : (__u32)total;
}

RISK_INLINE __u8 evaluate_tier(__u32 risk_q8)
{
    if (risk_q8 >= THRESHOLD_TIER3)
        return TIER_3_QUARANTINE;
    if (risk_q8 >= THRESHOLD_TIER2)
        return TIER_2_HOSTILE;
    if (risk_q8 >= THRESHOLD_TIER1)
        return TIER_1_SUSPICIOUS;
    return TIER_0_NORMAL;
}

#endif /* __AEGIS_RISK_H__ */
