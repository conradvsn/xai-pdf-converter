#!/bin/bash
# Script pour nettoyer et réexporter les credentials Adobe correctement

echo "Nettoyage des anciennes variables..."
unset ADOBE_CLIENT_ID
unset ADOBE_CLIENT_SECRET

echo "Export des nouvelles credentials (sans guillemets)..."
export ADOBE_CLIENT_ID='ac5748f0093b47578faba5ec311ab522'
export ADOBE_CLIENT_SECRET='p8e-1gG9zTfzmu3tVv_uSEglTDLdV3kPPaw_'

echo "✅ Credentials exportées correctement!"
echo ""
echo "Vérification:"
echo "ADOBE_CLIENT_ID (premiers 20 chars): ${ADOBE_CLIENT_ID:0:20}"
echo "ADOBE_CLIENT_SECRET (premiers 20 chars): ${ADOBE_CLIENT_SECRET:0:20}"
echo ""
echo "Si les valeurs ne commencent PAS par un guillemet, c'est bon!"
echo ""
echo "Maintenant, dans ce même terminal, lancez:"
echo "  python main.py"
