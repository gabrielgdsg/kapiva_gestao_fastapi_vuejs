# Pedidos Chegando — Fluxo Reverso de Imagens

## Problema atual

- Pedidos Chegando busca imagens no MongoDB (coleção Produto).
- A maioria dos itens são **produtos novos** que ainda não existem no catálogo.
- O catálogo (Produto) é alimentado pelo levantamento/estoque, que só recebe dados quando a NF é cadastrada.

## Solução proposta: fluxo reverso

A lógica deve ser **invertida**:

1. **Pedidos Chegando como fonte primária** — Ao sincronizar e extrair um pedido do PDF, salvar os produtos (ref, cor, marca, descrição, imagem) no MongoDB como **pré-cadastro**.
2. **Imagens do PDF** — Usar `extraction/pdf_images.py` para extrair imagens dos PDFs e associá-las aos itens extraídos pelo Gemini.
3. **Quando a NF chegar** — O sistema já terá os dados do pedido. Ao cadastrar a NF:
   - Fazer match por ref/cor/marca entre NF e pedidos pré-cadastrados.
   - Calcular confiança (probabilidade de a NF corresponder àquele pedido).
   - Avisar o usuário: "NF provavelmente do Pedido #X (conf. 95%)" ou "Possível divergência: ref na NF difere do pedido".
4. **Ajustes manuais** — Permitir vincular/desvincular NF ↔ pedido e ajustar ref/cor quando houver pequenas diferenças.

## Passos de implementação

### Fase 1 — Salvar produtos no MongoDB durante o sync

- [ ] Criar modelo/coleção `ProdutoPreCadastro` ou usar `Produto` com flag `origem: "pedido_chegando"`.
- [ ] Durante `sync_pedidos_chegando`, após extrair itens do PDF:
  - Extrair imagens do PDF (`pdf_images.extract_images_from_pdf`).
  - Associar imagens aos itens (por posição ou heurística).
  - Inserir/atualizar no MongoDB: `cod_referencia`, `nom_marca`, `des_cor`, `des_produto`, `img`, `pedido_id`, `order_ref`.
- [ ] Endpoint para listar pré-cadastros por pedido.

### Fase 2 — Match NF ↔ Pedido

- [ ] Ao cadastrar NF (levantamentos/estoque), buscar pedidos com mesma marca e refs similares.
- [ ] Calcular score de confiança (ex.: refs iguais = 100%, 1 ref diferente = 80%, etc.).
- [ ] Exibir aviso na tela de cadastro: "Este pedido pode corresponder ao Pedido #X (conf. 92%)".

### Fase 3 — Ajustes e vínculos

- [ ] UI para vincular NF a um pedido específico.
- [ ] UI para ajustar ref/cor quando a NF tiver pequenas diferenças.
- [ ] Histórico de matches (NF X ↔ Pedido Y).

## Arquivos relevantes

- `backend/extraction/pdf_images.py` — Extração de imagens do PDF.
- `backend/extraction/ai_extractor.py` — Extração de itens (ref, nome, cor, qty) via Gemini.
- `backend/app/api/pedidos_chegando/api_pedidos_chegando.py` — Sync e persistência.
- `db_mongo/` — Modelos ODMantic (Produto, etc.).
- `backend/app/api/levantamentos/` — Cadastro de NF e levantamentos.
