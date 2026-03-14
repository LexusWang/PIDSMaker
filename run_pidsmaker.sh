#!/usr/bin/env bash
set -e

LOG_DIR=./log/training_full
SYSTEMS=(velox flash orthrus kairos magic nodlink orthrus rcaid threatrace)
ATTACKS=(training_full_aa23_341a training_full_aa24_046a training_full_alphvblackcat training_full_phobosransomware)

mkdir -p "${LOG_DIR}"

for sys in "${SYSTEMS[@]}"; do
    echo "[+] Training ${sys} on training_full..."
    python -u pidsmaker/main.py "${sys}" training_full --stop_after=gnn_training 2>&1 | tee "${LOG_DIR}/${sys}_training_full.log"

    for attack in "${ATTACKS[@]}"; do
        echo "[+] Running ${sys} on ${attack}..."
        python -u pidsmaker/main.py "${sys}" "${attack}" --force_restart gnn_inference 2>&1 | tee "${LOG_DIR}/${sys}_${attack}.log"
    done
done

echo "[+] All tasks finished."
