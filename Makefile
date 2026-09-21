CC ?= gcc
CLANG ?= clang
BPFTOOL ?= bpftool

CFLAGS ?= -g -O2 -Wall
BPF_CFLAGS ?= -g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf

LIBBPF_LIBS ?= -lbpf -lm -lelf -lz

BPF_OBJ = bpf/p2_fs.bpf.o
SKEL_HDR = agent/p2_fs.skel.h
AGENT_BIN = bin/aegisd-fs
TEST_RISK_BIN = bin/test_risk
ENTROPY_RUNNER_BIN = bin/entropy_test_runner

AGENT_SRCS = agent/main.c agent/entropy_table.c agent/canary.c agent/policy.c agent/events.c

.PHONY: all clean test

all: dirs $(AGENT_BIN) $(TEST_RISK_BIN) $(ENTROPY_RUNNER_BIN)

dirs:
	@mkdir -p bin

# 1. Compile eBPF C program to BPF object
$(BPF_OBJ): bpf/p2_fs.bpf.c bpf/common.h bpf/lib/entropy.h bpf/lib/risk.h bpf/vmlinux.h
	@echo "  BPF      $@"
	@$(CLANG) $(BPF_CFLAGS) -c $< -o $@

# 2. Generate libbpf C skeleton header
$(SKEL_HDR): $(BPF_OBJ)
	@echo "  GEN-SKEL $@"
	@$(BPFTOOL) gen skeleton $< > $@

# 3. Compile userspace agent
$(AGENT_BIN): $(SKEL_HDR) $(AGENT_SRCS) agent/agent.h bpf/common.h
	@echo "  CC       $@"
	@$(CC) $(CFLAGS) -Iagent -Ibpf $(AGENT_SRCS) -o $@ $(LIBBPF_LIBS)

# 4. Compile risk unit tests
$(TEST_RISK_BIN): tests/unit/test_risk.c bpf/lib/risk.h bpf/common.h
	@echo "  CC       $@"
	@$(CC) $(CFLAGS) -Ibpf $< -o $@

# 5. Compile differential entropy test runner
$(ENTROPY_RUNNER_BIN): tests/unit/entropy_test_runner.c
	@echo "  CC       $@"
	@$(CC) $(CFLAGS) $< -o $@ -lm

# 6. Run all unit and differential tests
test: all
	@echo "=== Running Risk Unit Tests ==="
	@$(TEST_RISK_BIN)
	@echo "=== Running Differential Entropy Tests ==="
	@python3 tests/differential/compare_entropy.py

clean:
	@rm -rf bin $(BPF_OBJ) $(SKEL_HDR)
	@echo "Cleaned build artifacts."
