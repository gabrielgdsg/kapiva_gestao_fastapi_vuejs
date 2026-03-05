# Pedidos Chegando — Pipeline no backend

Depois de seguir o guia em `Downloads/PEDIDOS_CHEGANDO_PIPELINE.md` (passos 1–3 no Google Cloud e credenciais OAuth2):

## Passo 4 — Script de autorização (uma vez)

1. Coloque `client_secret.json` (baixado do Google Cloud) em `backend/`.
2. Use o ambiente virtual (já criado em `backend/.venv` com as dependências):
   ```bash
   cd backend
   .venv/bin/python gmail/auth.py
   ```
   (Se não existir `.venv`, crie com: `python3 -m venv .venv` e depois `.venv/bin/pip install google-auth-oauthlib google-auth-httplib2`.)
3. O script abre o navegador para você autorizar; copie as três linhas impressas para o `.env`.
4. Copie as três linhas impressas para o `backend/.env`.

## Passo 5 — Variáveis no `.env`

No `backend/.env` (ou no `develop_pycharm.env` na raiz do projeto), adicione:

- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (saída do auth.py)
- `GMAIL_ADDRESS=seu_email@gmail.com` (conta que você autorizou)
- `GEMINI_API_KEY=...` (opcional; para extrair dados dos PDFs — crie em https://aistudio.google.com)
- `ANTHROPIC_API_KEY=...` (opcional; fallback com Claude para PDFs difíceis)

## Passo 6 — Testar a conexão Gmail

```bash
cd backend
.venv/bin/python test_gmail.py
# Deve imprimir: ✓ Conexão OK — N e-mails com 'pedido' encontrados
```

## Armazenamento (não é MongoDB)

Os pedidos são salvos em **arquivo JSON** (`backend/uploads/pedidos_chegando.json`), não em MongoDB. Os PDFs ficam em `backend/uploads/pedidos_chegando_pdfs/{order_id}.pdf`.

**Docker:** O `docker-compose.dev.yml` monta `./backend/uploads:/app/uploads` para que os dados persistam entre reinícios do container. Sem esse volume, os pedidos seriam perdidos a cada restart.

## Uso no app

- **GET /api/pedidos-chegando** — Lista os pedidos (armazenados em `backend/uploads/pedidos_chegando.json`).
- **POST /api/pedidos-chegando/sync** — Busca e-mails no Gmail (assunto com "pedido", "order", etc.), extrai texto dos PDFs anexos, envia para o Gemini e salva os pedidos. A aba "Pedidos Chegando" no frontend chama isso ao clicar em "Sincronizar agora".
- **PATCH /api/pedidos-chegando/order/{id}** — Atualiza status (ex.: `{"status": "confirmed"}` ou `{"status": "needs-review"}` para voltar à caixa de entrada).
- **DELETE /api/pedidos-chegando/order/{id}** — Exclui o pedido permanentemente.

Sem `GEMINI_API_KEY`, o sync ainda busca os e-mails e lista quantos encontrou, mas não extrai itens dos PDFs.

## Fluxo reverso de imagens (planejado)

Hoje, Pedidos Chegando tenta buscar imagens no MongoDB (Produto), mas a maioria dos itens são produtos novos que ainda não existem lá. A lógica ideal é **inversa**:

1. **Durante o sync** — Extrair imagens dos PDFs e salvar no MongoDB como pré-cadastro de produtos (ref, cor, marca, img).
2. **Quando a NF chegar** — O sistema já terá os dados; ao cadastrar a NF, fazer o match e avisar o usuário com base na confiança (probabilidade de a NF corresponder àquele pedido).
3. **Ajustes** — Permitir ajustes manuais quando ref/cor da NF diferir ligeiramente do pedido.

Ver `PEDIDOS_CHEGANDO_REVERSE_IMAGES.md` para o plano de implementação.
