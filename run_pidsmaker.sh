#!/usr/bin/env bash
set -e

LOG_DIR=./log/new

echo "[+] Running kairos on PROVATTACK18..."
python -u pidsmaker/main.py kairos PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/kairos18.log"

echo "[+] Running magic on PROVATTACK18..."
python -u pidsmaker/main.py magic PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/magic18.log"

echo "[+] Running flash on PROVATTACK18..."
python -u pidsmaker/main.py flash PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/flash18.log"

echo "[+] Running nodlink on PROVATTACK18..."
python -u pidsmaker/main.py nodlink PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/nodlink18.log"

echo "[+] Running orthrus on PROVATTACK18..."
python -u pidsmaker/main.py orthrus PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/orthrus18.log"

echo "[+] Running rcaid on PROVATTACK18..."
python -u pidsmaker/main.py rcaid PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/rcaid18.log"

echo "[+] Running threatrace on PROVATTACK18..."
python -u pidsmaker/main.py threatrace PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/threatrace18.log"

echo "[+] Running velox on PROVATTACK18..."
python -u pidsmaker/main.py velox PROVATTACK18 2>&1 | tee "${LOG_DIR}/18/velox18.log"

echo "[+] Running kairos on PROVATTACK15..."
python -u pidsmaker/main.py kairos PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/kairos15.log"

echo "[+] Running magic on PROVATTACK15..."
python -u pidsmaker/main.py magic PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/magic15.log"

echo "[+] Running flash on PROVATTACK15..."
python -u pidsmaker/main.py flash PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/flash15.log"

echo "[+] Running nodlink on PROVATTACK15..."
python -u pidsmaker/main.py nodlink PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/nodlink15.log"

echo "[+] Running orthrus on PROVATTACK15..."
python -u pidsmaker/main.py orthrus PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/orthrus15.log"

echo "[+] Running rcaid on PROVATTACK15..."
python -u pidsmaker/main.py rcaid PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/rcaid15.log"

echo "[+] Running threatrace on PROVATTACK15..."
python -u pidsmaker/main.py threatrace PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/threatrace15.log"

echo "[+] Running velox on PROVATTACK15..."
python -u pidsmaker/main.py velox PROVATTACK15 2>&1 | tee "${LOG_DIR}/15/velox15.log"

echo "[+] All tasks finished."
