# Levantamentos MongoDB Sync

Levantamentos data can be synced from PostgreSQL to MongoDB for faster reads on Levantamentos2, especially for brands with many products (e.g. Beira Rio).

## How it works

1. **PostgreSQL** remains the source of truth.
2. **MongoDB** stores a cache of levantamentos per `(data_ini, data_fim, cod_marca)`.
3. When "MongoDB" is enabled in Levantamentos2, the API reads from MongoDB first (fast). If not found or stale (>24h), it falls back to PostgreSQL.

## Usage

### In Levantamentos2 UI

1. **Force Sync** – Click "Force Sync" to copy current selection (date range + marca) from Postgres to MongoDB.
2. **MongoDB** – Check the "MongoDB" checkbox to prefer reading from cache. Subsequent loads will be faster.

### API Endpoints

- **POST** `/api/levantamentos/sync?data_ini=YYYY-MM-DD&data_fim=YYYY-MM-DD&cod_marca=123`  
  Force sync for a specific marca and date range.

- **POST** `/api/levantamentos/sync-all?data_ini=YYYY-MM-DD&data_fim=YYYY-MM-DD`  
  Sync all marcas for the date range. Use for daily cron.

### Daily sync (cron)

Example cron to sync daily at 2am:

```bash
0 2 * * * curl -X POST "http://localhost:8000/api/levantamentos/sync-all?data_ini=2019-01-01&data_fim=2027-12-31"
```

Adjust `data_ini` and `data_fim` to your typical date range. The sync runs per marca and may take a few minutes for many marcas.
