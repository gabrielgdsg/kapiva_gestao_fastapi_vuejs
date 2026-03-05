# Upgrade MongoDB 4.4 → 6.0 (mantendo dados)

O MongoDB 4.4 está end-of-life. Este guia faz backup, sobe MongoDB 6 e restaura os dados.

**Caminho oficial:** 4.4 → 5.0 → 6.0 (não pode pular versão).  
**Abordagem aqui:** backup com `mongodump` + instalação limpa do 6.0 + `mongorestore` — evita problemas de compatibilidade.

---

## Pré-requisitos

- Docker instalado no PC Windows (192.168.1.170)
- MongoDB atual rodando (4.4.4) com `root` / `rootpassword`
- Backend e frontend podem ficar parados durante o upgrade

---

## Passo 1: Backup

No PowerShell, na pasta do projeto:

```powershell
# Criar pasta para o backup
New-Item -ItemType Directory -Force -Path C:\mongo_backup

# Fazer backup (MongoDB 4.4 precisa estar rodando)
docker run --rm -v C:\mongo_backup:/backup mongo:6 mongodump --uri="mongodb://root:rootpassword@host.docker.internal:27017" --out=/backup
```

Se o MongoDB estiver em outro host, troque `host.docker.internal` pelo IP (ex: `192.168.1.170`).

Confirme que a pasta `C:\mongo_backup` tem arquivos (ex.: pastas por database).

---

## Passo 2: Parar o MongoDB antigo

Pare o container ou serviço do MongoDB 4.4. Exemplo se for container:

```powershell
docker stop <nome_do_container_mongo>
# ou, se usar compose:
# docker compose -f <seu_compose> stop mongo
```

---

## Passo 3: Subir MongoDB 6 com volume novo

Use o compose abaixo ou crie um container manualmente.

**Opção A – Compose (recomendado)**

Crie `docker-compose.mongodb.yml`:

```yaml
services:
  mongo:
    image: mongo:6
    container_name: kapiva-mongo
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: rootpassword
    volumes:
      - mongo_data:/data/db
    ports:
      - "27017:27017"

volumes:
  mongo_data: {}
```

Suba:

```powershell
docker compose -f docker-compose.mongodb.yml up -d
```

Aguarde alguns segundos para o MongoDB iniciar.

**Opção B – Container manual**

```powershell
docker run -d --name kapiva-mongo -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=root -e MONGO_INITDB_ROOT_PASSWORD=rootpassword -v mongo_data:/data/db mongo:6
```

---

## Passo 4: Restaurar o backup

```powershell
docker run --rm -v C:\mongo_backup:/backup mongo:6 mongorestore --uri="mongodb://root:rootpassword@host.docker.internal:27017" /backup
```

Se o MongoDB estiver em outro host, use o IP correspondente no lugar de `host.docker.internal`.

---

## Passo 5: Conferir

Conecte no MongoDB (Compass ou `mongosh`) e verifique se os dados estão corretos.

---

## Passo 6: Subir backend e frontend

```powershell
docker compose -f docker-compose.network-remote.yml up -d
```

---

## Se algo der errado

1. Pare o MongoDB 6.
2. Volte o MongoDB 4.4 como estava antes.
3. O backup em `C:\mongo_backup` continua disponível para nova tentativa.

---

## Resumo dos comandos (PowerShell)

```powershell
# 1. Backup
New-Item -ItemType Directory -Force -Path C:\mongo_backup
docker run --rm -v C:\mongo_backup:/backup mongo:6 mongodump --uri="mongodb://root:rootpassword@host.docker.internal:27017" --out=/backup

# 2. Parar MongoDB antigo (ajuste o nome do container)
docker stop <container_mongo_antigo>

# 3. Subir MongoDB 6
docker compose -f docker-compose.mongodb.yml up -d

# 4. Aguardar ~10 segundos, depois restaurar
docker run --rm -v C:\mongo_backup:/backup mongo:6 mongorestore --uri="mongodb://root:rootpassword@host.docker.internal:27017" /backup

# 5. Subir app
docker compose -f docker-compose.network-remote.yml up -d
```
