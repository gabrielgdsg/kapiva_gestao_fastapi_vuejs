# Cartão / Conciliação (Stone + Sicredi Máquinas)

O endpoint `/api/financeiro/caixacartao/{data}` retorna o total de vendas em cartão somando Stone e Sicredi Máquinas.

## Stone

Configuração via variáveis de ambiente (ou usa valores padrão legados):

- `STONE_AFFILIATION_CODE` – Código de afiliação (StoneCode)
- `STONE_BEARER_TOKEN` – Token Bearer
- `STONE_AUTH_RAW` – Dados de autorização
- `STONE_AUTH_ENCRYPTED` – Dados criptografados

## Sicredi Máquinas

Para incluir Sicredi, configure no `.env`:

- `SICREDI_API_URL` – URL base da API de conciliação Sicredi
- `SICREDI_API_TOKEN` – Token de autenticação
- `SICREDI_ESTABELECIMENTO_ID` – ID do estabelecimento (se necessário)

**Nota:** A estrutura da API Sicredi pode variar. Se a sua API retornar JSON em outro formato, será necessário ajustar `_get_sicredi_cartao` em `api_caixa.py` para mapear corretamente o valor total (ex.: `valor`, `total`, `transacoes[].valor`).

Consulte o [Portal do Desenvolvedor Sicredi](https://portal-api-cooperativas.sicredi.com.br/) ou o suporte Sicredi Máquinas para obter a documentação da API de conciliação.
