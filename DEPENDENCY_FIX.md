# Dependency Version Fix Required

## Issue
Environment has incompatible versions:
- **Installed:** Pydantic v2.12.5, ODMantic v1.0.2
- **Required:** Pydantic v1.10.9, ODMantic v0.9.2 (from requirements.txt)

## Error
```
TypeError: field Config is defined without type annotation
```

This happens because ODMantic v1.0.2 with Pydantic v2 has compatibility issues with nested `Config` classes.

## Fix: Install Correct Versions

Run these commands to align with requirements.txt:

```bash
# Uninstall incompatible versions
pip uninstall pydantic pydantic-settings odmantic -y

# Install correct versions from requirements.txt
pip install pydantic==1.10.9
pip install odmantic==0.9.2

# Verify
python -c "import pydantic; print('Pydantic:', pydantic.__version__)"
python -c "import odmantic; print('ODMantic:', odmantic.__version__)"
```

## After Fix

Then update `backend/app/config.py` to use Pydantic v1 syntax:

```python
from pydantic import BaseSettings  # Simple - works with v1.10.9

class Settings(BaseSettings):
    # ... fields ...
    
    class Config:
        env_file = '../../develop_pycharm.env'
        extra = "ignore"
```

## Why This Matters

- COMISSAO models (single source of truth) won't work until versions are aligned
- All ODMantic models fail to import
- Business logic is preserved by using the versions the code was written for
