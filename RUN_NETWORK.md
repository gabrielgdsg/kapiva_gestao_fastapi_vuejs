# Rodar Kapiva em outro PC (mesma rede)

## Pré-requisitos
- Docker e Docker Compose instalados no PC de destino
- Projeto copiado para o PC (ou clonado do repositório)

## Opção 1: Stack completa (PostgreSQL + MongoDB no Docker)

O app roda com bancos locais no próprio Docker. **Atenção:** PostgreSQL e MongoDB começam vazios. Se precisar dos dados do PC principal, exporte/importe manualmente.

### 1. Configurar ambiente
```bash
cd /caminho/para/kapiva_fixed

# Criar .env.network (já vem com defaults)
cp backend/.env.network.example backend/.env.network

# Editar se precisar (senhas, etc.)
# nano backend/.env.network
```

### 2. Build e subir
```bash
docker compose -f docker-compose.network.yml up -d --build
```

### 3. Acessar
- **Neste PC:** http://localhost
- **Outros PCs na rede:** http://\<IP_DESTE_PC\>:80  
  (ex: http://192.168.1.100:80)

Para ver o IP:
```bash
# Linux
hostname -I | awk '{print $1}'
# ou
ip addr
```

---

## Opção 2: Usar PostgreSQL e MongoDB remotos (recomendado)

**Mesmos dados do seu host** – PostgreSQL em 192.168.1.151 e MongoDB em 192.168.1.170. Sem perda de dados.

```bash
docker compose -f docker-compose.network-remote.yml up -d --build
```

O `backend/.env.network` já está configurado para esses IPs. Edite se precisar alterar senhas ou endereços.

---

## Parar
```bash
docker compose -f docker-compose.network.yml down
```

## Ver logs
```bash
docker compose -f docker-compose.network.yml logs -f
```
