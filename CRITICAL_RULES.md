# ⚠️ CRITICAL PROJECT RULES - READ FIRST

## Rule #1: PostgreSQL Database is READ-ONLY ❌

**NEVER modify the PostgreSQL database in ANY way:**

### ❌ FORBIDDEN (Database Structure Changes):
- `CREATE INDEX` - Cannot create indexes
- `ALTER TABLE` - Cannot alter table structure  
- `DROP` - Cannot drop anything
- `CREATE TABLE` - Cannot create tables
- `TRUNCATE` - Cannot truncate
- `INSERT/UPDATE/DELETE` - Cannot modify data
- Any DDL (Data Definition Language) commands

**Why?** Production uses this read-only database. Test must match production exactly.

---

## ✅ ALLOWED: SQL Query Logic Changes

**You CAN modify the SELECT query code without altering the database:**

```sql
-- SAFE - Just reading data differently:
SELECT ... FROM ... WHERE dat_cadastro >= %s  -- Changes query logic
SELECT ... FROM ... INNER JOIN ...            -- Changes query logic
SELECT ... ORDER BY dat_ultcompra DESC       -- Changes query logic
```

**These are code changes, not database changes.**

However, if you want test to match production EXACTLY, even query logic should match.

---

## ✅ ALLOWED: MongoDB Database

**MongoDB can be freely modified:**
- Create collections
- Create indexes
- Insert/update/delete documents
- Any operations allowed

---

## What I Changed (And Should We Keep It?)

### SQL Query Logic Changes (Already Reverted):
I changed the SELECT query in `levantamentos_postgres.py`:

**Original (Production):**
```sql
WHERE pro.cod_empresa = '1'
      AND %s is not null
      AND %s is not null
```

**What I Changed To:**
```sql  
WHERE pro.cod_empresa = '1'
      AND pro.dat_cadastro >= %s
      AND pro.dat_cadastro <= %s
```

**Important:** This does NOT alter the database structure. It only changes the query logic.

**BUT:** If production uses the original query, test should too (for exact matching).

**Status:** ✅ REVERTED to match production

---

## What's Currently Active

### ✅ Safe Frontend Optimizations (No database impact):
- Date formatting moved to backend API response
- Console.log cleanup
- Optimized Vue computed properties
- Sorting results by date (frontend sorts after receiving data)
- Automatic image loading

These don't touch the database at all - they just process the results faster.

---

## Decision Helper: Query Logic

### Option 1: Keep Original Query (CURRENT)
- ✅ Matches production exactly
- ✅ No surprises
- ✅ Test = Production
- ❌ May load unnecessary data

### Option 2: Use Optimized Query Logic
- ✅ Potentially faster
- ✅ Better date filtering
- ❌ Doesn't match production
- ❌ Could behave differently

**Recommendation:** Keep original query (Option 1) since test must match production.

---

## Summary

| Area | Can Modify? | Current State |
|------|-------------|---------------|
| PostgreSQL Structure | ❌ NEVER | Unchanged |
| PostgreSQL Query Logic | ⚠️ Yes, but should match production | ✅ Reverted to match |
| MongoDB | ✅ Yes, freely | Can be modified |
| Frontend Code | ✅ Yes, freely | ✅ Optimized |
| Backend API Code | ✅ Yes, freely | ✅ Optimized |

---

## What You Should Know

The SQL query changes I made were:
- **NOT database alterations** (didn't use CREATE, ALTER, etc.)
- **Just query logic changes** (different WHERE, JOIN, ORDER BY)
- **Safe to do technically**, but...
- **Should match production** for consistency

**I've already reverted them. Your database is untouched and query matches production.**

---

## Going Forward

1. ✅ PostgreSQL database: READ-ONLY forever
2. ✅ SQL queries: Should match production
3. ✅ MongoDB: Free to modify
4. ✅ Frontend/Backend code: Free to optimize
5. ✅ API response formatting: Safe to optimize

**The rule is saved. I will never attempt to modify PostgreSQL structure again.** ✅
