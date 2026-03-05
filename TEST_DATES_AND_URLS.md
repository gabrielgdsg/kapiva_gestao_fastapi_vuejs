# 🎯 Test Dates & Correct URLs

## ⚠️ IMPORTANT: Use Port 80, NOT 8080!

**Everything is now on port 80:**
- ✅ **Correct:** http://localhost:80
- ❌ **Wrong:** http://localhost:8080 (old, not working)

---

## 📊 Database Date Ranges

### COMISSAO Table
- **Start Date:** 2019-07-26
- **End Date:** 2024-03-09
- **Total Records:** 111,842

### Recent Dates with Data (for testing)

| Date | Records | Total Sales |
|------|---------|-------------|
| 2024-03-09 | 122 | R$ 30,484.80 |
| 2024-03-08 | 82 | R$ 13,695.04 |
| 2024-03-07 | 78 | R$ 14,281.86 |
| 2024-03-06 | 71 | R$ 14,336.61 |
| 2024-03-01 | 80 | R$ 13,138.81 |

### Monthly Summary (2024)

| Month | Records | Total |
|-------|---------|-------|
| March 2024 | 581 | R$ 118,229.13 |
| February 2024 | 1,249 | R$ 243,893.92 |
| January 2024 | 1,191 | R$ 195,820.50 |

---

## 🔗 Correct URLs to Use

### Main Application
```
http://localhost:80/
```

### Comissão
```
http://localhost:80/comissao/selecionar
```

### Levantamentos Test2
```
http://localhost:80/levantamentos_test2/
```

### API Documentation
```
http://localhost:80/docs
```

---

## ✅ Recommended Test Scenarios

### Test 1: Single Day (Recent)
- **URL:** http://localhost:80/comissao/selecionar
- **Date:** 2024-03-09 to 2024-03-09
- **Expected:** 122 records, R$ 30,484.80

### Test 2: Single Week
- **URL:** http://localhost:80/comissao/selecionar
- **Date:** 2024-03-01 to 2024-03-09
- **Expected:** ~600 records

### Test 3: Full Month (Best for testing)
- **URL:** http://localhost:80/comissao/selecionar
- **Date:** 2024-02-01 to 2024-02-29
- **Expected:** 1,249 records, R$ 243,893.92

### Test 4: Year to Date
- **URL:** http://localhost:80/comissao/selecionar
- **Date:** 2024-01-01 to 2024-03-09
- **Expected:** ~2,000 records

---

## 🐛 If You Get 404 Error

**Problem:** Accessing http://localhost:8080
**Solution:** Change to http://localhost:80

The old Python HTTP server on port 8080 has been stopped. Everything now runs on port 80 (backend + frontend unified).

---

## 📝 Quick Checklist

- [ ] Close any tabs with `localhost:8080`
- [ ] Open `http://localhost:80`
- [ ] Test Comissão with date range: 2024-02-01 to 2024-02-29
- [ ] Test Levantamentos Test2 with marca autocomplete
- [ ] Verify marcas dropdown shows 1,978 brands

---

**All tests should now work on port 80!** 🎉
