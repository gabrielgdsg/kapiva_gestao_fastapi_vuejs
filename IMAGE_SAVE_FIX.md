# 🖼️ Image Save Fix

## Problem Identified
When the user pasted an image URL into the `img_link` field and clicked "Salvar Produtos", they received a **422 Unprocessable Entity** error.

## Root Cause
The `img_link` field used `v-model` to update `subgrouped_items_bycolor_obj`, but the `saveProdutos()` function sent `produtosSelecionados`, which is computed from `todosProdutos`. The manually entered image URL was **never synced** to `todosProdutos`, so it wasn't included in the save request.

```
User types image URL 
    ↓
Updates: subgrouped_items_bycolor_obj[ref][cor][0].img
    ↓
Clicks "Salvar Produtos"
    ↓
Sends: produtosSelecionados (computed from todosProdutos)
    ❌ Image URL is NOT in todosProdutos!
```

## Solution Implemented
Modified `saveProdutos()` to **pull the latest `img` value** from `subgrouped_items_bycolor_obj` before sending the save request:

```javascript
async saveProdutos() {
    // Update img from subgrouped_items_bycolor_obj before saving
    const produtosToSave = this.produtosSelecionados.map(produto => {
        // Get the latest img value from the view object
        const currentImg = this.subgrouped_items_bycolor_obj[produto.cod_referencia]?.[produto.des_cor]?.[0]?.img;
        return {
            ...produto,
            img: currentImg || produto.img // Use current img or fallback to original
        };
    });

    const api_path = `/api/produtos/save`
    axios.put(api_path, produtosToSave)
        .then(() => {
            alert('Produtos salvos com sucesso!');
        })
        .catch((error) => {
            console.error('Erro ao salvar produtos:', error);
            alert('Erro ao salvar produtos. Verifique o console.');
        })
}
```

## How to Test
1. Select a product (checkbox)
2. Show "Img Link" column if hidden
3. Paste an image URL (base64 or http) into the `img_link` field
4. Click "Salvar Produtos"
5. ✅ Should see "Produtos salvos com sucesso!" alert
6. Refresh page - image should persist

## Additional Improvements
- Added success alert when products are saved
- Added error alert with console logging for debugging
- Used optional chaining (`?.`) to prevent errors if product not found

---

## About the 9076.102 Data Difference

**User Concern:** "Something seems strange, compare 9076.102 in these two screenshots"

**Explanation:** This is **CORRECT and EXPECTED** behavior! The two screenshots show:

1. **Screenshot 1:** Date range `01/01/2022 - 31/01/2024` 
   - Shows full movimento history for 2+ years
   
2. **Screenshot 2:** Date range `01/01/2024 - 03/01/2026`
   - Shows only recent movimento from 2024 onwards

The **size counts are different** because `movimento` (stock movements) are **filtered by the selected date range**. This is exactly how the application should work - you're seeing different data because you selected different dates!

The SQL query correctly includes `produto_ficha_estoq` (movimento) data filtered by the date range, which is why the entrada counts change based on your date selection.
