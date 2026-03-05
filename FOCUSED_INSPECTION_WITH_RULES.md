# Focused Code Inspection - Respecting PROJECT_RULES.md

## Context Understanding

After reviewing PROJECT_RULES.md, this is a **retail inventory management system** (not quant trading - that appears to be template text). Key business constraints:

1. **COMISSAO table is single source of truth** (Section 9.1) - MUST PRESERVE
2. **All performance metrics use COMISSAO.base_calc_comissao** (Section 10.1) - MUST PRESERVE  
3. **Date alignment:** commission recognition date vs sales date (Section 9.2)
4. **Business logic must not change** - only safety/quality improvements allowed

## Inspection Philosophy

Following PROJECT_RULES Section 8:
> "Inspect this project **as-is**, explain exactly what it does, list hidden assumptions, identify fragile areas, and propose improvements **without changing strategy behavior** unless explicitly justified."

## ✅ SAFE TO IMPROVE (No Business Logic Impact)

### 1. Security - CORS Configuration ⚠️ CRITICAL
**File:** `backend/app/main.py:36-43`
**Impact:** Security only, no business logic
**Risk Level:** SAFE - Changes infrastructure, not calculations

**Current:**
```python
origins = ['*']  # SECURITY RISK
```

**Fix:** Allow-list specific origins (respects all business rules)

### 2. Hardcoded Credentials - Remove from Code ⚠️ CRITICAL  
**File:** `backend/app/main.py:29-33`, `api_caixa.py:138-140`
**Impact:** Security only, no business logic
**Risk Level:** SAFE - Cleanup only

**Current:** Passwords and API keys in commented code
**Fix:** Remove commented credentials (already using env vars)

### 3. Error Handling - Don't Expose Internals ⚠️ HIGH
**Files:** Multiple API endpoints
**Impact:** Better error messages, no logic change
**Risk Level:** SAFE - Same logic, better presentation

**Current:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Exposes internal errors
```

**Fix:** Log internally, return generic message (no calculation changes)

### 4. Logging System - Add Structured Logging ⚠️ HIGH
**Files:** Throughout
**Impact:** Better observability, no business logic
**Risk Level:** SAFE - Adds logging, doesn't change calculations

**Current:** Using `print()` statements
**Fix:** Add proper logging (won't affect COMISSAO calculations)

### 5. Database Connection Pool Error Handling ⚠️ HIGH
**File:** `backend/app/db_postgres/connection.py`
**Impact:** Resilience only, no query logic change
**Risk Level:** SAFE - Adds error handling, same queries

**Current:** No error handling for pool exhaustion
**Fix:** Add try/catch with proper errors (COMISSAO queries unchanged)

### 6. Duplicate Import Bug ⚠️ MEDIUM
**File:** `backend/app/api/estoque/api_estoque.py:10`
**Impact:** Bug fix, no business logic
**Risk Level:** SAFE - Removes duplicate, no calculation change

**Current:**
```python
from datetime import datetime, timedelta  # line 8
import orjson, datetime  # line 10 - DUPLICATE!
```

**Fix:** Remove duplicate (already correctly imported on line 8)

### 7. Debug Code Removal ⚠️ MEDIUM
**Files:** `api_estoque.py:194,382`, `api_caixa.py:121-122`
**Impact:** Cleanup only, no business logic
**Risk Level:** SAFE - Removes debug statements

**Current:**
```python
if produto.des_tamanho == '39-42':
    print('pause')  # Debug code
```

**Fix:** Remove debug code (doesn't affect COMISSAO calculations)

### 8. Input Validation - Preserve COMISSAO Logic ⚠️ MEDIUM
**Files:** Date inputs in various endpoints
**Impact:** Better validation, same calculations
**Risk Level:** SAFE - Validates before querying, COMISSAO queries unchanged

**Note:** Must ensure date validation doesn't change how dates are interpreted for COMISSAO queries

### 9. Deprecated Pydantic Settings ⚠️ MEDIUM
**File:** `backend/app/config.py`
**Impact:** Library update, no business logic
**Risk Level:** SAFE - Same config values, different import

**Current:**
```python
from pydantic import BaseSettings  # Deprecated
```

**Fix:** Use `pydantic_settings` (same values, different import)

### 10. Type Hints Addition ⚠️ LOW
**Files:** Throughout
**Impact:** Code quality only, no runtime change
**Risk Level:** SAFE - Additive only

## ⛔ MUST NOT CHANGE (Business Logic - PROJECT_RULES)

### 1. COMISSAO Query Logic ❌ DO NOT MODIFY
**Files:** 
- `backend/app/api/comissao/comissao_postgres.py:7-18`
- `backend/app/api/comissao/api_comissao.py:23,28`
- `backend/app/api/vendas/api_vendas.py:10-18`

**Why:** PROJECT_RULES Section 9.1 states "COMISSAO table is the single source of truth"
**Current Queries are CORRECT:**
```python
# This query MUST NOT be changed - it's the source of truth
SELECT A.cod_vendedor, AB.nom_usuario AS nom_vendedor, 
       sum(a.base_calc_comissao) AS base_calculo  # Single source of truth
FROM COMISSAO A
```

**Action:** Only improve error handling around these queries, never change the SQL logic

### 2. base_calc_comissao Calculations ❌ DO NOT MODIFY
**Files:** Throughout codebase
**Why:** PROJECT_RULES Section 10.1 - "Faturamento Real" source is `COMISSAO.base_calc_comissao`
**Action:** Preserve all uses of `base_calc_comissao` exactly as-is

### 3. Date Handling for COMISSAO ❌ BE CAREFUL
**Files:** `api_comissao.py`, date-related queries
**Why:** PROJECT_RULES Section 9.2 - Date alignment assumptions (sales date vs commission recognition)
**Current Logic:**
```python
WHERE A.dat_emissao >= %s AND A.dat_emissao <= %s  # Must preserve this
```

**Action:** Can add validation, but must preserve `dat_emissao` field usage

### 4. Commission Tiers (1%, 1.2%, 1.5%) ❌ DO NOT MODIFY
**Why:** PROJECT_RULES Section 9.3 - Business rule
**Action:** If found in code, preserve exactly

### 5. Promotion Logic ❌ DO NOT MODIFY
**Why:** PROJECT_RULES Section 9.5 - Complex business rules about inventory age and promotions
**Action:** Don't touch promotion calculation logic

### 6. Inventory Aging Calculations ❌ BE CAREFUL
**Why:** PROJECT_RULES Section 10.2 - "Dias em Estoque" has specific bucketing (0-90, 91-180, etc.)
**Action:** If modifying estoque code, preserve aging buckets

## 🔍 Verification Checklist

Before implementing any change, verify:

- [ ] Does NOT modify COMISSAO table queries
- [ ] Does NOT change base_calc_comissao usage
- [ ] Does NOT alter date field interpretation (dat_emissao)
- [ ] Does NOT change commission tier percentages
- [ ] Does NOT modify promotion calculation logic
- [ ] Does NOT alter inventory aging buckets
- [ ] Only adds safety/validation/error handling
- [ ] Only improves code quality (logging, type hints, etc.)

## Implementation Priority (Safe Changes Only)

### Phase 1: Critical Security (0 business logic impact)
1. ✅ Fix CORS configuration
2. ✅ Remove hardcoded credentials  
3. ✅ Add error handling without exposing internals

### Phase 2: Resilience (0 business logic impact)
4. ✅ Add database pool error handling
5. ✅ Add logging system
6. ✅ Remove debug code

### Phase 3: Code Quality (0 business logic impact)
7. ✅ Fix duplicate imports
8. ✅ Update deprecated Pydantic
9. ✅ Add type hints
10. ✅ Add input validation (preserving date logic)

## Files That Handle COMISSAO (Be Extra Careful)

These files directly interact with the single source of truth - modify with extreme caution:

1. `backend/app/api/comissao/comissao_postgres.py` - SQL queries ⚠️
2. `backend/app/api/comissao/api_comissao.py` - API endpoints ⚠️
3. `backend/app/api/vendas/api_vendas.py` - Uses COMISSAO table ⚠️
4. `backend/app/api/models/comissao.py` - Data models ⚠️

**Rule:** Only add error handling/logging. Do NOT modify:
- SQL WHERE clauses
- Field selections
- Aggregation logic (SUM, GROUP BY)
- Date field usage (dat_emissao)

## Implementation Plan

### Step 1: Backup ✅ DONE
- Created: `backup_pre_refactor_20260110_102604`
- Git status checked

### Step 2: Safe Improvements (Starting Now)
Implementing only changes that:
- Improve security
- Add error handling
- Fix bugs
- Add logging
- **DO NOT** change business calculations

### Step 3: Verification After Each Change
- Run existing tests (if any)
- Verify COMISSAO queries still work
- Check that calculations match before/after

---

**Inspection Date:** Today  
**Inspector:** Code Analysis (Sonnet-focused with PROJECT_RULES constraints)  
**Next Action:** Begin Phase 1 safe improvements
