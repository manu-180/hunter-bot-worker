#!/bin/bash

echo "======================================================================"
echo "HUNTERBOT - DUAL WORKER LAUNCHER"
echo "======================================================================"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "Starting both workers in background..."
echo "======================================================================"
echo ""

# Iniciar domain_hunter_worker.py en background
echo "[LAUNCHER] Starting Domain Hunter Worker..."
python -u domain_hunter_worker.py 2>&1 | sed 's/^/[DOMAIN-HUNTER] /' &
DOMAIN_PID=$!
echo "[LAUNCHER] Domain Hunter PID: $DOMAIN_PID"

# Esperar un poco para que inicie
sleep 2

# Iniciar main.py en background
echo "[LAUNCHER] Starting LeadSniper Worker..."
python -u main.py 2>&1 | sed 's/^/[LEADSNIPER] /' &
LEADSNIPER_PID=$!
echo "[LAUNCHER] LeadSniper PID: $LEADSNIPER_PID"

echo ""
echo "[LAUNCHER] Both workers started successfully!"
echo "[LAUNCHER] Domain Hunter PID: $DOMAIN_PID"
echo "[LAUNCHER] LeadSniper PID: $LEADSNIPER_PID"
echo "======================================================================"
echo ""

# Función para manejar señales de terminación
cleanup() {
    echo ""
    echo "[LAUNCHER] Termination signal received. Stopping workers..."
    kill $DOMAIN_PID $LEADSNIPER_PID 2>/dev/null
    wait $DOMAIN_PID $LEADSNIPER_PID 2>/dev/null
    echo "[LAUNCHER] Workers stopped."
    exit 0
}

# Registrar handler para SIGTERM y SIGINT
trap cleanup SIGTERM SIGINT

# Esperar a que ambos procesos terminen (nunca deberían)
wait $DOMAIN_PID $LEADSNIPER_PID
