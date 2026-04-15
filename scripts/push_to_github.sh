#!/usr/bin/env bash
set -e

REPO_URL="https://Ferelking242:${GITHUB_PAT}@github.com/Ferelking242/watchtower.git"
SOURCE_DIR="/home/runner/workspace/mangayomi"
WORK_DIR="/tmp/watchtower_push"

echo "==> Préparation du dossier de travail..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

echo "==> Copie des sources (hors .git)..."
cp -a "$SOURCE_DIR/." "$WORK_DIR/"
rm -rf "$WORK_DIR/.git" "$WORK_DIR/build" "$WORK_DIR/.dart_tool"

echo "==> Initialisation du dépôt git..."
cd "$WORK_DIR"
git init
git config user.email "replit-agent@watchtower.dev"
git config user.name "Replit Agent"

echo "==> Ajout de tous les fichiers..."
git add -A

echo "==> Commit..."
git commit -m "feat: rebrand to Watchtower - replace all mangayomi references"

echo "==> Push vers GitHub..."
git remote add origin "$REPO_URL"
git push -u origin main --force

echo "==> Push terminé avec succès!"
