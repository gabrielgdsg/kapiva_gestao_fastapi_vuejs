# Deploy Kapiva no Windows (192.168.1.170)

## Opção A: Via LAN (recomendado — mais simples)

### 1. Primeira vez no PC Windows

1. **Instale** Docker Desktop no Windows: https://docs.docker.com/desktop/install/windows-install/

2. **Copie o projeto** para o PC Windows:
   - **Via Git (recomendado):** `git clone <seu-repo> C:\kapiva` — evita .venv e symlinks
   - **Via SMB/rede:** NÃO copie estas pastas (têm symlinks que o Windows/SMB não suporta):
     - `backend/.venv` (ambiente Python — o Docker cria o seu)
     - `frontend/node_modules` (dependências — o Docker instala)
     - `backend/uploads` (dados locais — opcional)
     - `db_mongo/data` (dados MongoDB locais)
   - Ao copiar manualmente: use "Skip" ou "Skip All" nos erros de symlink, ou exclua `.venv` antes

3. **Crie o arquivo** `backend\.env.network` no PC Windows (copie do Linux e ajuste):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=LOGTEC
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
MONGODB_URL=mongodb://mongo:27017
# Opcional: timeout (ms) e fallback para JSON quando Mongo indisponível (rede instável)
# MONGODB_TIMEOUT_MS=15000
# MONGODB_FALLBACK_JSON=true
UVICORN_HOST=0.0.0.0
ENV=production
ALLOWED_ORIGINS=*

# Opcional: Pedidos Chegando (Gmail)
# GOOGLE_CLIENT_ID=...
# GOOGLE_CLIENT_SECRET=...
# GOOGLE_REFRESH_TOKEN=...
# GEMINI_API_KEY=...
```

4. **Suba os containers** (no diretório do projeto):

```powershell
docker compose -f docker-compose.network.yml up -d --build
```

5. **Acesse** em qualquer PC da rede: http://192.168.1.170

---

### 2. Enviar atualizações (LAN)

**No Linux (seu PC):**
```bash
# Empacote e envie via rsync/scp (se tiver SSH no Windows)
rsync -avz --exclude node_modules --exclude __pycache__ --exclude .git \
  ./ user@192.168.1.170:C:/kapiva/

# Ou use compartilhamento de pasta SMB e copie manualmente
# Ou: git push e no Windows: git pull
```

**No Windows (PC 192.168.1.170):**
```powershell
# Se usar Git:
git pull
.\update.ps1

# Ou manualmente:
docker compose -f docker-compose.network.yml up -d --build
```

---

### 2b. Atualizar tudo pelo terminal (Linux → Windows via SSH)

Se o Windows tiver **OpenSSH** habilitado, você pode atualizar o host Docker inteiramente do seu PC:

```bash
# 1. No seu PC (Linux): commit e push das alterações
git add -A && git commit -m "update" && git push

# 2. Conectar no Windows e atualizar (substitua USER pelo usuário Windows)
ssh USER@192.168.1.170 "cd C:/kapiva_fixed && git pull && docker compose -f docker-compose.network-remote-with-mongo.yml up -d --build"
```

Ou, se preferir enviar arquivos sem Git:

```bash
# Enviar código e subir containers em um comando
rsync -avz --exclude node_modules --exclude __pycache__ --exclude .venv --exclude .git \
  ./ USER@192.168.1.170:C:/kapiva_fixed/ && \
ssh USER@192.168.1.170 "cd C:/kapiva_fixed && docker compose -f docker-compose.network-remote-with-mongo.yml up -d --build"
```

**Habilitar SSH no Windows** (se ainda não tiver):
- Configurações → Aplicativos → Recursos opcionais → Adicionar recurso → **Cliente OpenSSH** e **Servidor OpenSSH**
- Ou: `Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0`

---

## Opção B: Via Docker Hub

Útil se quiser atualizar de qualquer lugar, sem acesso à rede local.

### 1. No Linux (build e push)

```bash
# Login (uma vez)
docker login

# Build e tag (substitua SEU_USUARIO pelo seu usuário Docker Hub)
docker compose -f docker-compose.network.yml build
docker tag kapiva-backend:latest SEU_USUARIO/kapiva-backend:latest
docker tag kapiva-frontend:latest SEU_USUARIO/kapiva-frontend:latest

docker push SEU_USUARIO/kapiva-backend:latest
docker push SEU_USUARIO/kapiva-frontend:latest
```

### 2. No Windows (primeira vez)

- Crie `backend\.env.network` como na Opção A
- Use `docker-compose.hub.yml` (veja abaixo)
- `docker compose -f docker-compose.hub.yml up -d`

### 3. Atualizar no Windows

```powershell
docker compose -f docker-compose.hub.yml pull
docker compose -f docker-compose.hub.yml up -d
```

---

## Resumo: qual usar?

| Método | Prós | Contras |
|--------|------|---------|
| **LAN (Git + update.ps1)** | Simples, sem conta externa, build local | Precisa estar na rede ou ter Git |
| **Docker Hub** | Atualiza de qualquer lugar | Rate limit free tier, precisa build para linux/amd64 |

**Recomendação:** Use **LAN + Git**. No Windows: `git pull` + `.\update.ps1`. Rápido e direto.

---

## Opção C: Postgres remoto + MongoDB em container

Se o **PostgreSQL** está em outra máquina (ex.: 192.168.1.151) e você quer **MongoDB em container**:

```powershell
docker compose -f docker-compose.network-remote-with-mongo.yml up -d --build
```

- Postgres: remoto (192.168.1.151) — configure em `backend/.env.network`
- MongoDB: container local com volume `mongo_data`

---

## Erro: "The container name /kapiva-mongo is already in use"

Se aparecer **"Conflict. The container name '/kapiva-mongo' is already in use"**:

- **Causa:** Um container antigo com esse nome ainda existe (ex.: de outra pasta ou compose).
- **Solução:** Remova o container antigo. Os dados ficam no **volume** `mongo_data`, não no container — remover o container **não apaga** os dados.

```powershell
# Remover apenas o container conflitante (dados permanecem no volume)
docker rm -f kapiva-mongo

# Se houver conflito com postgres também:
docker rm -f kapiva-postgres

# Depois suba de novo
docker compose -f docker-compose.network.yml up -d --build
```

**Importante:** Use `docker rm` (remove container). **Não** use `docker compose down -v` — o `-v` remove os volumes e apaga os dados.

---

## Erro: "Symlinks not supported" ao copiar via SMB

Se aparecer **"Error while copying 'lib64'"** ou **"Error while copying 'python3'"** com "Symlinks not supported by backend":

- **Causa:** A pasta `backend/.venv` tem symlinks (links simbólicos) que o SMB/Windows não copia.
- **Solução:** Use **"Skip All"** — a pasta `.venv` não é necessária no Windows. O Docker monta o código e instala as dependências dentro do container.
- **Melhor:** Use **Git clone** no Windows em vez de copiar. O `.venv` está no `.gitignore`, então não será clonado.
