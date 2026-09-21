#include "agent.h"

struct canary_def {
    const char *rel_name;
    const char *magic_hdr;
    size_t hdr_len;
    size_t file_size;
};

static const struct canary_def CANARY_TEMPLATES[] = {
    {"!00_SystemConfig.docx", "PK\x03\x04\x14\x00", 6, 16384},
    {"00_TaxReturn_2026.pdf", "%PDF-1.7\n", 9, 32768},
    {"_0_CorporateSecrets.xlsx", "PK\x03\x04\x14\x00", 6, 20480},
    {"0_FamilyPhoto_Archive.jpg", "\xFF\xD8\xFF\xE0\x00\x10JFIF", 10, 65536},
    {"!_Credentials_Vault.txt", "Aegis Decoy File - DO NOT MODIFY\n", 33, 4096}
};

#define NUM_CANARIES (sizeof(CANARY_TEMPLATES) / sizeof(CANARY_TEMPLATES[0]))

int init_canaries(int map_fd, const char *canary_dir)
{
    char dir_buf[512];
    if (!canary_dir)
        canary_dir = "/tmp/aegis_canaries";

    snprintf(dir_buf, sizeof(dir_buf), "%s", canary_dir);
    mkdir(dir_buf, 0777);
    chmod(dir_buf, 0777);

    int registered = 0;
    for (size_t i = 0; i < NUM_CANARIES; i++) {
        char path[1024];
        snprintf(path, sizeof(path), "%s/%s", dir_buf, CANARY_TEMPLATES[i].rel_name);

        FILE *fp = fopen(path, "wb");
        if (!fp) {
            fprintf(stderr, "[-] Warning: Failed to create canary file %s\n", path);
            continue;
        }

        /* Write signature */
        fwrite(CANARY_TEMPLATES[i].magic_hdr, 1, CANARY_TEMPLATES[i].hdr_len, fp);

        /* Write filler bytes */
        size_t remaining = CANARY_TEMPLATES[i].file_size - CANARY_TEMPLATES[i].hdr_len;
        char filler[256];
        memset(filler, 'A' + (i % 26), sizeof(filler));
        while (remaining > 0) {
            size_t to_write = remaining > sizeof(filler) ? sizeof(filler) : remaining;
            fwrite(filler, 1, to_write, fp);
            remaining -= to_write;
        }
        fclose(fp);
        chmod(path, 0666);

        /* Stat the file to get dev and ino */
        struct stat st;
        if (stat(path, &st) == 0) {
            struct devino_key key = {
                .dev = (uint32_t)st.st_dev,
                .ino = (uint64_t)st.st_ino
            };
            uint8_t val = 1;
            if (bpf_map_update_elem(map_fd, &key, &val, BPF_ANY) == 0) {
                registered++;
                printf("[+] Canary registered: %s (dev: %u, ino: %llu)\n",
                       CANARY_TEMPLATES[i].rel_name, key.dev, (unsigned long long)key.ino);
            } else {
                fprintf(stderr, "[-] Failed to register canary in BPF map: %s\n", path);
            }
        }
    }

    printf("[+] Total decoy canaries active: %d in %s\n", registered, dir_buf);
    return registered > 0 ? 0 : -1;
}
