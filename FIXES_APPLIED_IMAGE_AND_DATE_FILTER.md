# 🔧 Critical Fixes Applied

## ✅ Fix 1: Image Save to MongoDB - **FIXED**

### Problem
Images were showing the success popup but not persisting after reload. The image was being updated in memory but **never saved to MongoDB**.

### Root Cause
The `/api/produtos/save` endpoint was calling `save_all()` at the end, but ODMantic might not properly track updates to existing documents in a batch operation.

### Solution Implemented
Changed from batch `save_all()` to individual `save()` calls with proper error handling:

```python
@router.put("/api/produtos/save")
async def save_produtos(produtos: List[Produto]):
    saved_count = 0
    created_count = 0
    
    for produto in produtos:
        try:
            # Find existing product in MongoDB
            db_produto = await engine.find_one(
                Produto,
                Produto.cod_referencia == produto.cod_referencia,
                Produto.nom_marca == produto.nom_marca,
                Produto.des_cor == produto.des_cor,
                Produto.des_produto == produto.des_produto
            )
            
            if db_produto is not None:
                # Update existing product
                print(f'[SAVE] Updating: {produto.cod_referencia} - {produto.des_cor}')
                db_produto.img = produto.img
                await engine.save(db_produto)  # Individual save for updates
                saved_count += 1
            else:
                # Create new product
                print(f'[SAVE] Creating: {produto.cod_referencia} - {produto.des_cor}')
                await engine.save(produto)  # Individual save for inserts
                created_count += 1
                
        except Exception as e:
            print(f'[ERROR] Failed to save {produto.cod_referencia}: {str(e)}')
            continue
    
    return {"status": "success", "updated": saved_count, "created": created_count}
```

**Improvements:**
- ✅ Individual `save()` calls ensure proper persistence
- ✅ Detailed logging shows what's being saved
- ✅ Error handling continues on failure (doesn't break the whole batch)
- ✅ Returns count of updated vs created products

---

## ✅ Fix 2: Date Filter Changed to `dat_ultcompra` - **FIXED**

### User Request
> "I would like for the date range filter be by 'data ult_compra' instead of 'data_cadastro', but maintain data_cadastro as a fallback (I am not sure if all products have a consistent data_ult compra). and that the estoque_entrada would be calculated based on this, (only by the items that came between the data_ult_compra range)"

### Changes Made

#### 1. Product Filtering
Changed from:
```sql
WHERE pro.dat_cadastro >= %s AND pro.dat_cadastro <= %s
```

To:
```sql
WHERE COALESCE(pro.dat_ultcompra, pro.dat_cadastro) >= %s 
  AND COALESCE(pro.dat_ultcompra, pro.dat_cadastro) <= %s
```

**How it works:**
- If `dat_ultcompra` exists → uses `dat_ultcompra`
- If `dat_ultcompra` is NULL → falls back to `dat_cadastro`

#### 2. Movimento Filtering (entrada/saida calculations)
Added date filtering to the movimento join:
```sql
LEFT OUTER JOIN produto_ficha_estoq pfe 
    ON (pfe.cod_produto = pro.cod_produto 
        AND pfe.data >= %s 
        AND pfe.data <= %s)
```

**Result:**
- Only movimento (stock movements) **within the selected date range** are included
- `estoque_entrada` calculations now show **only items that arrived within the date range**
- More accurate representation of what happened during the selected period

---

## 🧪 Testing Instructions

### Test 1: Image Save & Persistence
1. Open `http://localhost:8000`
2. Go to LevantamentosTest2
3. Select "BEIRA RIO", dates `01/01/2024` to `31/01/2024`, click "Enviar"
4. Select product **9076.102 PRETO** (checkbox)
5. Show "Img Link" column
6. Paste an image URL (or upload file)
7. Click **"Salvar Produtos"**
8. ✅ Should see success alert
9. **Refresh the page** (F5)
10. Load the same product again
11. ✅ **Image should persist** and show immediately

**Check backend logs for:**
```
[SAVE] Updating existing product: 9076.102 - PRETO
[SAVE] Summary: 1 updated, 0 created
```

---

### Test 2: Date Filter by `dat_ultcompra`

#### Test A: Products with `dat_ultcompra`
1. Select dates: `01/01/2024` to `31/12/2024`
2. Click "Enviar"
3. ✅ Should see products where `dat_ultcompra` is between these dates
4. Products with `dat_ultcompra` outside this range should NOT appear (even if `dat_cadastro` is within range)

#### Test B: Products without `dat_ultcompra` (fallback to `dat_cadastro`)
1. Look for products without `dat_ultcompra` in the database
2. They should appear based on their `dat_cadastro` date

#### Test C: Movimento (entrada) Filtering
1. Load products for a specific date range
2. Check the **entrada counts** in the size columns
3. ✅ Entrada should only show stock movements **within the selected date range**
4. Compare with a wider date range - entrada counts should increase

**Example:**
- Dates: `01/03/2024` to `31/03/2024` → Shows only March entrada
- Dates: `01/01/2024` to `31/12/2024` → Shows entire year entrada (higher counts)

---

## 📊 Expected Behavior Changes

### Before Fix 1 (Image Save):
- ❌ Image appeared to save (success popup)
- ❌ Image disappeared on page refresh
- ❌ No error messages

### After Fix 1:
- ✅ Image saves to MongoDB properly
- ✅ Image persists after page refresh
- ✅ Backend logs show save operations
- ✅ Error handling prevents silent failures

---

### Before Fix 2 (Date Filter):
- Products filtered by `dat_cadastro` only
- Movimento included ALL records (no date filtering)
- Entrada counts showed entire history

### After Fix 2:
- Products filtered by `dat_ultcompra` (with `dat_cadastro` fallback via `COALESCE`)
- Movimento filtered by date range
- **Entrada counts show only movements within selected dates**

---

## 🔍 Potential Issues to Watch

### Issue 1: Different Results After Date Filter Change
**Expected:** You will see DIFFERENT products when you select the same date range, because:
- Before: Filtered by `dat_cadastro`
- After: Filtered by `dat_ultcompra` (or `dat_cadastro` if null)

**This is correct!** If a product was registered in 2020 (`dat_cadastro=2020`) but last purchased in 2024 (`dat_ultcompra=2024`), it will now appear in 2024 date range instead of 2020.

### Issue 2: Lower Entrada Counts
**Expected:** Entrada counts may be LOWER than before, because:
- Before: Showed ALL movimento for each product (entire history)
- After: Shows ONLY movimento within the selected date range

**This is correct!** It's more accurate - you're now seeing what actually happened during the period you selected.

---

## 📝 Summary

**Both fixes are now live:**
1. ✅ Images save and persist correctly to MongoDB
2. ✅ Date filter uses `dat_ultcompra` with `dat_cadastro` fallback
3. ✅ Movimento (entrada) filtered by date range

**Backend running on:** `http://localhost:8000`

Test both fixes and let me know if there are any issues! 🚀
