#!/bin/bash
# Script pour déployer la correction psycopg sur Render

echo "🔧 Correction de l'erreur psycopg2 pour Render"
echo ""
echo "Changements appliqués :"
echo "  ✅ runtime.txt : Python 3.11.9 (compatible Render)"
echo "  ✅ requirements.txt : psycopg[binary] v3 au lieu de psycopg2"
echo "  ✅ config.py : Configuration optimisée pour PostgreSQL"
echo ""
echo "📦 Ajout des fichiers au commit..."
git add runtime.txt requirements.txt config.py DEPLOY_RENDER.md

echo "💾 Création du commit..."
git commit -m "Fix: Resolve psycopg2 ImportError with Python 3.11 and psycopg v3"

echo "🚀 Push vers GitHub..."
git push origin main

echo ""
echo "✅ Correction déployée !"
echo ""
echo "📊 Prochaines étapes :"
echo "  1. Allez sur render.com/dashboard"
echo "  2. Votre service va se redéployer automatiquement"
echo "  3. Vérifiez les logs (devrait démarrer sans erreur)"
echo "  4. Testez : curl https://votre-app.onrender.com/health"
echo ""
echo "⏱️  Le redéploiement prend environ 3-5 minutes."
