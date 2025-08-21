#!/usr/bin/env python3
"""
Test Supabase Connection Script
Kiểm tra kết nối database trước khi migration
"""

import psycopg2
from sqlalchemy import create_engine, text
import sys

# Your Supabase database URL
DATABASE_URL = "postgresql://postgres.qnnwnqsitsyegqeceypk:5uGkDiIthYfb3kx1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

def test_direct_connection():
    """Test direct psycopg2 connection"""
    try:
        print("🔗 Testing direct psycopg2 connection...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Direct connection successful!")
        print(f"📊 PostgreSQL version: {version[0][:50]}...")
        
        # Test database info
        cursor.execute("SELECT current_database(), current_user;")
        db_info = cursor.fetchone()
        print(f"📁 Database: {db_info[0]}")
        print(f"👤 User: {db_info[1]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Direct connection failed: {str(e)}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    try:
        print("\n🔗 Testing SQLAlchemy connection...")
        
        # Ensure correct format for SQLAlchemy
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(
            db_url,
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"sslmode": "require"}
        )
        
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ SQLAlchemy connection successful!")
            print(f"📊 Version: {version[0][:50]}...")
            
            # Test schema info
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = result.fetchall()
            print(f"📋 Existing tables: {len(tables)}")
            for table in tables[:5]:  # Show first 5 tables
                print(f"   - {table[0]}")
            if len(tables) > 5:
                print(f"   ... and {len(tables) - 5} more")
        
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {str(e)}")
        return False

def test_permissions():
    """Test database permissions"""
    try:
        print("\n🔐 Testing database permissions...")
        
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Test CREATE TABLE permission
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS test_permissions (
                        id SERIAL PRIMARY KEY,
                        test_data VARCHAR(50)
                    )
                """))
                print("✅ CREATE TABLE permission: OK")
                
                # Test INSERT permission
                conn.execute(text("""
                    INSERT INTO test_permissions (test_data) 
                    VALUES ('test_migration')
                """))
                print("✅ INSERT permission: OK")
                
                # Test SELECT permission
                result = conn.execute(text("SELECT COUNT(*) FROM test_permissions"))
                count = result.fetchone()[0]
                print(f"✅ SELECT permission: OK (found {count} records)")
                
                # Test UPDATE permission
                conn.execute(text("""
                    UPDATE test_permissions 
                    SET test_data = 'test_updated' 
                    WHERE test_data = 'test_migration'
                """))
                print("✅ UPDATE permission: OK")
                
                # Test DELETE permission
                conn.execute(text("DELETE FROM test_permissions WHERE test_data = 'test_updated'"))
                print("✅ DELETE permission: OK")
                
                # Clean up test table
                conn.execute(text("DROP TABLE IF EXISTS test_permissions"))
                print("✅ DROP TABLE permission: OK")
                
                conn.commit()
                
            except Exception as e:
                print(f"❌ Permission test failed: {str(e)}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Permission test error: {str(e)}")
        return False

def test_performance():
    """Test basic performance"""
    try:
        print("\n⚡ Testing basic performance...")
        
        import time
        db_url = DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        
        engine = create_engine(db_url)
        
        # Test connection time
        start_time = time.time()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        connection_time = time.time() - start_time
        
        print(f"🚀 Connection time: {connection_time:.3f} seconds")
        
        if connection_time < 1.0:
            print("✅ Connection speed: Excellent")
        elif connection_time < 3.0:
            print("✅ Connection speed: Good")
        else:
            print("⚠️ Connection speed: Slow (but acceptable)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 SUPABASE CONNECTION TEST")
    print("=" * 50)
    print(f"🎯 Target: db.qnnwnqsitsyegqeceypk.supabase.co")
    print(f"🔗 Database: postgres")
    print("=" * 50)
    
    tests = [
        ("Direct Connection", test_direct_connection),
        ("SQLAlchemy Connection", test_sqlalchemy_connection),
        ("Database Permissions", test_permissions),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if not success:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your Supabase database is ready for migration!")
        print("\n🚀 Next steps:")
        print("   1. Run: python production_migration_script.py")
        print("   2. Test your app: streamlit run app.py")
        print("   3. Deploy to Streamlit Cloud")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️ Please fix the issues before proceeding with migration.")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your database URL")
        print("   2. Verify network connectivity")
        print("   3. Confirm database permissions")
        print("   4. Contact Supabase support if needed")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)