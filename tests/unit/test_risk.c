#include <stdio.h>
#include <assert.h>
#include <stdint.h>
#include "../../bpf/lib/risk.h"

void test_decay_halves_every_half_life(void)
{
    __u32 initial_risk = 100 << 8; /* 100.0 in Q8 */
    __u32 decayed = decay_risk_q8(initial_risk, HALF_LIFE_MS);
    assert(decayed == (initial_risk >> 1));
    printf("[PASS] test_decay_halves_every_half_life\n");
}

void test_evidence_caps_at_max(void)
{
    __u32 initial_risk = RISK_MAX - 100;
    __u32 updated = apply_evidence_q8(initial_risk, 40 << 8, 256);
    assert(updated == RISK_MAX);
    printf("[PASS] test_evidence_caps_at_max\n");
}

void test_tier_threshold_boundaries(void)
{
    assert(evaluate_tier(0) == TIER_0_NORMAL);
    assert(evaluate_tier(THRESHOLD_TIER1 - 1) == TIER_0_NORMAL);
    assert(evaluate_tier(THRESHOLD_TIER1) == TIER_1_SUSPICIOUS);
    assert(evaluate_tier(THRESHOLD_TIER2 - 1) == TIER_1_SUSPICIOUS);
    assert(evaluate_tier(THRESHOLD_TIER2) == TIER_2_HOSTILE);
    assert(evaluate_tier(THRESHOLD_TIER3 - 1) == TIER_2_HOSTILE);
    assert(evaluate_tier(THRESHOLD_TIER3) == TIER_3_QUARANTINE);
    printf("[PASS] test_tier_threshold_boundaries\n");
}

int main(void)
{
    printf("=== Aegis Risk Engine Unit Tests ===\n");
    test_decay_halves_every_half_life();
    test_evidence_caps_at_max();
    test_tier_threshold_boundaries();
    printf("=== All Risk Unit Tests Passed! ===\n");
    return 0;
}
