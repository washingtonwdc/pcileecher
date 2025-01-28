#!/bin/bash

# Verificar se o nome do secret foi fornecido
if [ -z "$1" ]; then
    echo "Error: Secret name is required"
    echo "Usage: ./create-secret.sh SECRET_NAME SECRET_VALUE"
    exit 1
fi

# Verificar se o valor do secret foi fornecido
if [ -z "$2" ]; then
    echo "Error: Secret value is required"
    echo "Usage: ./create-secret.sh SECRET_NAME SECRET_VALUE"
    exit 1
fi

SECRET_NAME=$1
SECRET_VALUE=$2

# Criar o secret
echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" \
    --data-file=- \
    --replication-policy="automatic"

echo "Secret '$SECRET_NAME' created successfully"
