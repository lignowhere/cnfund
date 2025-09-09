#!/usr/bin/env python3
"""
Test NAV sorting logic
"""

from datetime import datetime, date
from models import Transaction

class MockTransaction:
    def __init__(self, id, date_str, nav, tx_type="NAV Update"):
        self.id = id
        self.date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        self.nav = nav
        self.type = tx_type

def test_nav_sorting():
    """Test the new smart sorting logic"""
    
    print("🧪 Testing NAV Sorting Logic")
    print("=" * 50)
    
    # Create test transactions similar to our real data
    transactions = [
        MockTransaction(31, "2025-09-09 17:58:20", 3856151478, "NAV Update"),  # Suspicious timestamp
        MockTransaction(44, "2025-09-09 11:48:12", 3857151478, "NAV Update"),  # Our target
        MockTransaction(40, "2025-09-09 11:32:17", 3859151478, "NAV Update"),  
        MockTransaction(39, "2025-09-09 11:26:05", 3858151478, "NAV Update"),
        MockTransaction(29, "2025-09-09 16:55:41", 3852151478, "NAV Update"),
    ]
    
    print("Test transactions:")
    for t in transactions:
        print(f"  ID:{t.id:2d} | Date:{t.date} | NAV:{t.nav:>15,}")
    
    print(f"\n1. Original sorting (date, id) DESC:")
    def original_sort(tx):
        return (tx.date, tx.id)
    
    original_sorted = sorted(transactions, key=original_sort, reverse=True)
    for i, t in enumerate(original_sorted):
        marker = " <<<< SELECTED" if i == 0 else ""
        print(f"  {i+1}. ID:{t.id:2d} | Date:{t.date} | NAV:{t.nav:>15,}{marker}")
    
    print(f"\n2. ID-only sorting:")
    id_sorted = sorted(transactions, key=lambda x: x.id, reverse=True)
    for i, t in enumerate(id_sorted):
        marker = " <<<< SELECTED" if i == 0 else ""
        print(f"  {i+1}. ID:{t.id:2d} | Date:{t.date} | NAV:{t.nav:>15,}{marker}")
    
    print(f"\n3. Smart sorting (date only, then id):")
    def smart_sort(tx):
        tx_date = tx.date.date() if hasattr(tx.date, 'date') else tx.date
        return (tx_date, tx.id)
    
    smart_sorted = sorted(transactions, key=smart_sort, reverse=True)
    for i, t in enumerate(smart_sorted):
        marker = " <<<< SELECTED" if i == 0 else ""
        tx_date = t.date.date()
        print(f"  {i+1}. ID:{t.id:2d} | Date:{tx_date} | NAV:{t.nav:>15,}{marker}")
    
    # Test get_nav_for_date logic
    print(f"\n4. Testing get_nav_for_date:")
    
    test_dates = [
        date(2025, 9, 9),   # Today
        date(2025, 9, 8),   # Yesterday
        date(2025, 9, 10),  # Tomorrow
    ]
    
    for test_date in test_dates:
        print(f"\n   get_nav_for_date({test_date}):")
        
        relevant = []
        for t in transactions:
            tx_date = t.date.date()
            if tx_date <= test_date:
                relevant.append(t)
        
        if relevant:
            def sort_key(tx):
                tx_date = tx.date.date()
                return (tx_date, tx.id)
            
            sorted_relevant = sorted(relevant, key=sort_key, reverse=True)
            selected = sorted_relevant[0]
            
            print(f"     Selected: ID:{selected.id}, Date:{selected.date.date()}, NAV:{selected.nav:,}")
            print(f"     Candidates:")
            for t in sorted_relevant[:3]:  # Show top 3
                marker = " <<<< SELECTED" if t == selected else ""
                print(f"       ID:{t.id:2d} | Date:{t.date.date()} | NAV:{t.nav:>15,}{marker}")
        else:
            print(f"     No NAV found for {test_date}")

if __name__ == "__main__":
    test_nav_sorting()