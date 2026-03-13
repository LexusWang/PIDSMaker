#!/usr/bin/env bash
set -e

LOG_DIR=./log/training_full
SYSTEMS=(kairos magic flash nodlink orthrus rcaid threatrace velox)
ATTACKS=(training_full_aa23_341a training_full_aa24_046a training_full_alphvblackcat training_full_phobosransomware)

mkdir -p "${LOG_DIR}"

# Step 1: Train each system on benign data (training_full)
for sys in "${SYSTEMS[@]}"; do
    echo "[+] Training ${sys} on training_full..."
    python -u pidsmaker/main.py "${sys}" training_full 2>&1 | tee "${LOG_DIR}/${sys}_training_full.log"
done

# Step 2: Run inference on each attack for each system
for sys in "${SYSTEMS[@]}"; do
    for attack in "${ATTACKS[@]}"; do
        echo "[+] Running ${sys} on ${attack}..."
        python -u pidsmaker/main.py "${sys}" "${attack}" 2>&1 | tee "${LOG_DIR}/${sys}_${attack}.log"
    done
done

echo "[+] All tasks finished."
