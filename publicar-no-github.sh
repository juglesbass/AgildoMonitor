#!/usr/bin/env bash
# Envia alterações do AgildoMonitor para https://github.com/juglesbass/AgildoMonitor
# O código-fonte fica em ScriptsAgildo/ — NÃO envies a pasta build/ (só artefactos PyInstaller).
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RAIZ"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo 'Erro: não é um repositório git.' >&2
  exit 1
fi

VERSAO="$(tr -d '[:space:]' < version.txt)"
TAG="v${VERSAO}"

echo "Versão em version.txt: ${VERSAO}"
echo 'A enviar branch main…'
git push -u origin main

if git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null 2>&1; then
  echo "Etiqueta ${TAG} já existe localmente; a enviar…"
  git push origin "${TAG}" || echo "Se falhar, apaga a tag antiga no GitHub ou usa outra versão."
else
  git tag -a "${TAG}" -m "Release ${VERSAO}"
  git push origin "${TAG}"
fi

echo ''
echo "Feito. Verifica: https://github.com/juglesbass/AgildoMonitor/releases/tag/${TAG}"
