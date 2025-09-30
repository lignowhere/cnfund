# Import Update Guide

After reorganization, update imports in the following files:

## Files to Update
- `app.py`
- `pages/investor_page.py`
- `pages/transaction_page.py`
- `pages/fee_page_enhanced.py`
- `pages/report_page_enhanced.py`
- `pages/backup_page.py`

## Import Changes

| Old Import | New Import |
|------------|------------|
| `from auth_helper import ...` | `from utils.auth_helper import ...` |
| `import auth_helper` | `import utils.auth_helper` |
| `from auto_backup_personal import ...` | `from integrations.auto_backup_personal import ...` |
| `import auto_backup_personal` | `import integrations.auto_backup_personal` |
| `from cache_service_simple import ...` | `from performance.cache_service_simple import ...` |
| `import cache_service_simple` | `import performance.cache_service_simple` |
| `from chart_utils import ...` | `from ui.chart_utils import ...` |
| `import chart_utils` | `import ui.chart_utils` |
| `from color_coding import ...` | `from ui.color_coding import ...` |
| `import color_coding` | `import ui.color_coding` |
| `from csv_data_handler import ...` | `from core.csv_data_handler import ...` |
| `import csv_data_handler` | `import core.csv_data_handler` |
| `from datetime_utils import ...` | `from utils.datetime_utils import ...` |
| `import datetime_utils` | `import utils.datetime_utils` |
| `from error_tracker import ...` | `from utils.error_tracker import ...` |
| `import error_tracker` | `import utils.error_tracker` |
| `from google_drive_hybrid import ...` | `from integrations.google_drive_hybrid import ...` |
| `import google_drive_hybrid` | `import integrations.google_drive_hybrid` |
| `from google_drive_manager import ...` | `from integrations.google_drive_manager import ...` |
| `import google_drive_manager` | `import integrations.google_drive_manager` |
| `from google_drive_oauth import ...` | `from integrations.google_drive_oauth import ...` |
| `import google_drive_oauth` | `import integrations.google_drive_oauth` |
| `from lazy_loader import ...` | `from performance.lazy_loader import ...` |
| `import lazy_loader` | `import performance.lazy_loader` |
| `from models import ...` | `from core.models import ...` |
| `import models` | `import core.models` |
| `from navigation_optimizer import ...` | `from performance.navigation_optimizer import ...` |
| `import navigation_optimizer` | `import performance.navigation_optimizer` |
| `from performance_monitor import ...` | `from performance.performance_monitor import ...` |
| `import performance_monitor` | `import performance.performance_monitor` |
| `from save_optimization import ...` | `from core.save_optimization import ...` |
| `import save_optimization` | `import core.save_optimization` |
| `from security_manager import ...` | `from utils.security_manager import ...` |
| `import security_manager` | `import utils.security_manager` |
| `from services_enhanced import ...` | `from core.services_enhanced import ...` |
| `import services_enhanced` | `import core.services_enhanced` |
| `from sidebar_manager import ...` | `from ui.sidebar_manager import ...` |
| `import sidebar_manager` | `import ui.sidebar_manager` |
| `from skeleton_components import ...` | `from performance.skeleton_components import ...` |
| `import skeleton_components` | `import performance.skeleton_components` |
| `from state_manager import ...` | `from performance.state_manager import ...` |
| `import state_manager` | `import performance.state_manager` |
| `from streamlit_widget_safety import ...` | `from utils.streamlit_widget_safety import ...` |
| `import streamlit_widget_safety` | `import utils.streamlit_widget_safety` |
| `from styles import ...` | `from ui.styles import ...` |
| `import styles` | `import ui.styles` |
| `from timezone_manager import ...` | `from utils.timezone_manager import ...` |
| `import timezone_manager` | `import utils.timezone_manager` |
| `from type_safety_fixes import ...` | `from utils.type_safety_fixes import ...` |
| `import type_safety_fixes` | `import utils.type_safety_fixes` |
| `from ui_improvements import ...` | `from ui.ui_improvements import ...` |
| `import ui_improvements` | `import ui.ui_improvements` |
| `from ux_enhancements import ...` | `from ui.ux_enhancements import ...` |
| `import ux_enhancements` | `import ui.ux_enhancements` |
| `from virtual_scroll import ...` | `from performance.virtual_scroll import ...` |
| `import virtual_scroll` | `import performance.virtual_scroll` |


## Example Updates

### Before:
```python
from cache_service_simple import warm_cache
from performance_monitor import get_performance_monitor
from ux_enhancements import UXEnhancements
```

### After:
```python
from performance.cache_service_simple import warm_cache
from performance.performance_monitor import get_performance_monitor
from ui.ux_enhancements import UXEnhancements
```

## Automated Update Script
Run `python update_imports.py` to automatically update all imports.
