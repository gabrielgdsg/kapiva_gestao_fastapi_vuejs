# Pipeline: Pedidos Chegando (Gmail → PDF → Dados + Imagens)

## Objetivo

Receber pedidos por e-mail (PDFs com layout variável por marca), extrair **dados** (marca, ref, cor, itens, quantidades) e **imagens dos produtos** dos PDFs e carregar na aba "Pedidos Chegando" para busca (ex: "bota marrom a chegar este mês").

## Visão do fluxo

```
Gmail (IMAP/OAuth) → Backend
       │
       ├── Sync periódico (ex: 15 min) + Backfill histórico
       │
       ▼
  E-mails "pedido" / "NF-e"
       │
       ├── Anexos PDF → extração de imagens (PyMuPDF/pdf2image) + texto
       │
       ├── Dados estruturados: Gemini/Claude (layout diferente por marca)
       │   → brand, order_ref, delivery_date, itens (ref, name, color, qty)
       │
       ├── Imagens por item: associar imagem extraída do PDF ao ref+cor
       │   (cada marca coloca ref/cor perto da imagem no PDF)
       │
       ▼
  PostgreSQL (orders, order_items com image_path ou blob)
       │
       ▼
  Vue "Pedidos Chegando" (busca, filtros, imagens)
```

## Como obter imagens dos PDFs

1. **Bibliotecas**: `PyMuPDF` (fitz) ou `pdf2image` (poppler) para renderizar páginas em imagem.
2. **Por página**: extrair cada página como PNG/JPEG; usar **detecção de regiões** (caixas que contêm uma imagem + texto ref/cor ao lado) ou heurística por marca.
3. **Layout por marca**: cada fornecedor coloca marca no topo, ref e cor perto do produto. Possíveis abordagens:
   - **Template por marca**: definir regiões (x, y, w, h) por marca para cada “bloco produto”.
   - **IA (Gemini/Claude)**: enviar imagem da página + instrução “retorne as coordenadas das imagens de produto e o ref/cor de cada uma”.
4. **Salvar**: guardar em disco (`UPLOAD_DIR/orders/<order_id>/<ref>_<cor>.jpg`) ou em blob no PostgreSQL; `order_items.image_path` ou campo binário.

## E-mail

- **IMAP** ou **Gmail API** com OAuth2 (variáveis `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`).
- Filtrar por assunto/corpo: "pedido", "NF-e", "nota fiscal", "fatura", "remessa".
- Baixar anexos PDF; processar em job assíncrono para não travar a API.

## Backend (a implementar)

- **Tabelas**: ver arquitetura em `pipeline-architecture (1).md` (orders, order_items, supplier_transit_overrides, orphan_invoices).
- **Endpoints**:  
  - `GET /api/pedidos-chegando` → já existe (stub); passar a ler do PostgreSQL.  
  - `POST /api/pedidos-chegando/sync` → disparar sync Gmail + processamento de PDFs + extração de imagens.
- **Variáveis de ambiente**: ver seção 7 do `pipeline-architecture (1).md` (Gmail, Gemini, ANTHROPIC, DATABASE_URL, UPLOAD_DIR, etc.).

## Resumo

- **Sim, é possível** obter as imagens dos PDFs de pedido: extraindo as páginas como imagem e depois cortando/associando cada imagem ao ref+cor (por template por marca ou por IA).
- A aba **Pedidos Chegando** já existe no frontend com layout e cores do app; ao conectar o backend ao Gmail e à extração de PDFs (dados + imagens), os pedidos passarão a ser carregados e pesquisáveis (ex: “bota marrom a chegar este mês”) com as imagens exibidas.
