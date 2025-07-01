#!/usr/bin/env python3
"""
Database Health Check Script for Proxmox Environments
Monitors database connectivity, performance, and data integrity
"""

import os
import sys
import django
import time
import logging
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.db import connections, connection
from django.core.management import call_command
from django.conf import settings
from django.db.utils import OperationalError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseHealthChecker:
    def __init__(self):
        self.db_config = settings.DATABASES['default']
        self.issues = []
        
    def check_database_connection(self):
        """Test database connectivity"""
        print("🔌 Testing Database Connection...")
        print("=" * 40)
        
        try:
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    print("✅ Database connection successful")
                    
                    # Get database info
                    if self.db_config['ENGINE'] == 'django.db.backends.postgresql':
                        cursor.execute("SELECT version()")
                        version = cursor.fetchone()
                        print(f"   Database: PostgreSQL")
                        print(f"   Version: {version[0]}")
                    elif self.db_config['ENGINE'] == 'django.db.backends.sqlite3':
                        print(f"   Database: SQLite")
                        print(f"   File: {self.db_config['NAME']}")
                    
                    return True
                else:
                    print("❌ Database connection test failed")
                    return False
                    
        except OperationalError as e:
            print(f"❌ Database connection error: {e}")
            self.issues.append(f"Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected database error: {e}")
            self.issues.append(f"Unexpected error: {e}")
            return False
    
    def check_database_performance(self):
        """Test database performance"""
        print("\n⚡ Testing Database Performance...")
        print("=" * 40)
        
        try:
            with connection.cursor() as cursor:
                # Test query performance
                start_time = time.time()
                
                # Simple query
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                count = cursor.fetchone()[0]
                simple_query_time = time.time() - start_time
                
                print(f"✅ Simple query: {simple_query_time:.3f}s")
                
                # Test multiple queries
                start_time = time.time()
                for i in range(10):
                    cursor.execute("SELECT 1")
                multiple_query_time = time.time() - start_time
                
                print(f"✅ Multiple queries: {multiple_query_time:.3f}s")
                
                # Performance assessment
                if simple_query_time < 0.1 and multiple_query_time < 0.5:
                    print("✅ Database performance is good")
                    return True
                elif simple_query_time < 0.5 and multiple_query_time < 2.0:
                    print("⚠️ Database performance is acceptable")
                    return True
                else:
                    print("❌ Database performance is poor")
                    self.issues.append("Poor database performance")
                    return False
                    
        except Exception as e:
            print(f"❌ Performance test error: {e}")
            self.issues.append(f"Performance test error: {e}")
            return False
    
    def check_database_integrity(self):
        """Check database integrity"""
        print("\n🔍 Checking Database Integrity...")
        print("=" * 40)
        
        try:
            # Check if Django tables exist
            with connection.cursor() as cursor:
                if self.db_config['ENGINE'] == 'django.db.backends.postgresql':
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name LIKE 'django_%'
                    """)
                else:  # SQLite
                    cursor.execute("""
                        SELECT name 
                        FROM sqlite_master 
                        WHERE type='table' 
                        AND name LIKE 'django_%'
                    """)
                
                django_tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = [
                    'django_migrations',
                    'django_content_type',
                    'django_admin_log',
                    'auth_user',
                    'auth_group',
                    'auth_permission'
                ]
                
                missing_tables = [table for table in required_tables if table not in django_tables]
                
                if missing_tables:
                    print(f"❌ Missing Django tables: {missing_tables}")
                    self.issues.append(f"Missing tables: {missing_tables}")
                    return False
                else:
                    print("✅ All required Django tables exist")
                
                # Check application tables
                app_tables = [
                    'store_product',
                    'store_category',
                    'payment_order',
                    'payment_orderitem',
                    'cart_cart'
                ]
                
                existing_app_tables = []
                for table in app_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        existing_app_tables.append(table)
                        print(f"   {table}: {count} records")
                    except:
                        print(f"   {table}: ❌ Missing")
                
                if len(existing_app_tables) >= 3:
                    print("✅ Application tables are properly set up")
                    return True
                else:
                    print("❌ Missing application tables")
                    self.issues.append("Missing application tables")
                    return False
                    
        except Exception as e:
            print(f"❌ Integrity check error: {e}")
            self.issues.append(f"Integrity check error: {e}")
            return False
    
    def check_data_consistency(self):
        """Check data consistency"""
        print("\n📊 Checking Data Consistency...")
        print("=" * 40)
        
        try:
            from store.models import Product, Category
            from payment.models import Order, OrderItem
            
            # Check product data
            product_count = Product.objects.count()
            category_count = Category.objects.count()
            
            print(f"   Products: {product_count}")
            print(f"   Categories: {category_count}")
            
            # Check for orphaned data
            orphaned_products = Product.objects.filter(category__isnull=True).count()
            if orphaned_products > 0:
                print(f"   ⚠️ Orphaned products: {orphaned_products}")
                self.issues.append(f"Orphaned products: {orphaned_products}")
            
            # Check order data
            order_count = Order.objects.count()
            order_item_count = OrderItem.objects.count()
            
            print(f"   Orders: {order_count}")
            print(f"   Order Items: {order_item_count}")
            
            # Check for orders without items
            orders_without_items = Order.objects.filter(orderitem__isnull=True).count()
            if orders_without_items > 0:
                print(f"   ⚠️ Orders without items: {orders_without_items}")
                self.issues.append(f"Orders without items: {orders_without_items}")
            
            # Check recent activity
            recent_orders = Order.objects.filter(
                created_at__gte=datetime.now() - timedelta(days=7)
            ).count()
            
            print(f"   Recent orders (7 days): {recent_orders}")
            
            if product_count > 0 and order_count >= 0:
                print("✅ Data consistency check passed")
                return True
            else:
                print("❌ Data consistency issues detected")
                return False
                
        except Exception as e:
            print(f"❌ Data consistency check error: {e}")
            self.issues.append(f"Data consistency error: {e}")
            return False
    
    def check_migrations(self):
        """Check if all migrations are applied"""
        print("\n🔄 Checking Database Migrations...")
        print("=" * 40)
        
        try:
            # Check for unapplied migrations
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('showmigrations', stdout=output)
            migrations_output = output.getvalue()
            
            # Check for [X] (applied) vs [ ] (unapplied)
            unapplied = migrations_output.count('[ ]')
            applied = migrations_output.count('[X]')
            
            print(f"   Applied migrations: {applied}")
            print(f"   Unapplied migrations: {unapplied}")
            
            if unapplied == 0:
                print("✅ All migrations are applied")
                return True
            else:
                print("❌ Unapplied migrations detected")
                self.issues.append(f"Unapplied migrations: {unapplied}")
                return False
                
        except Exception as e:
            print(f"❌ Migration check error: {e}")
            self.issues.append(f"Migration check error: {e}")
            return False
    
    def check_database_size(self):
        """Check database size and growth"""
        print("\n💾 Checking Database Size...")
        print("=" * 40)
        
        try:
            with connection.cursor() as cursor:
                if self.db_config['ENGINE'] == 'django.db.backends.postgresql':
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)
                    size = cursor.fetchone()[0]
                    print(f"   Database size: {size}")
                    
                    # Check table sizes
                    cursor.execute("""
                        SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                        LIMIT 5
                    """)
                    
                    print("   Largest tables:")
                    for row in cursor.fetchall():
                        print(f"     {row[1]}: {row[2]}")
                        
                else:  # SQLite
                    import os
                    db_path = self.db_config['NAME']
                    if os.path.exists(db_path):
                        size_bytes = os.path.getsize(db_path)
                        size_mb = size_bytes / (1024 * 1024)
                        print(f"   Database size: {size_mb:.2f} MB")
                    else:
                        print("   Database file not found")
                        return False
                
                return True
                
        except Exception as e:
            print(f"❌ Size check error: {e}")
            self.issues.append(f"Size check error: {e}")
            return False
    
    def run_comprehensive_check(self):
        """Run all health checks"""
        print("🏥 Starting Database Health Check")
        print("=" * 50)
        print(f"Database: {self.db_config['ENGINE']}")
        print(f"Host: {self.db_config.get('HOST', 'localhost')}")
        print(f"Name: {self.db_config['NAME']}")
        print("=" * 50)
        
        checks = [
            ("Connection", self.check_database_connection),
            ("Performance", self.check_database_performance),
            ("Integrity", self.check_database_integrity),
            ("Data Consistency", self.check_data_consistency),
            ("Migrations", self.check_migrations),
            ("Size", self.check_database_size),
        ]
        
        results = []
        for check_name, check_func in checks:
            print(f"\n🔍 Running: {check_name}")
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                print(f"❌ Check failed with exception: {e}")
                results.append((check_name, False))
                self.issues.append(f"{check_name} check failed: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        passed = 0
        for check_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(results)} checks passed")
        
        if self.issues:
            print("\n⚠️ Issues Found:")
            for issue in self.issues:
                print(f"   • {issue}")
        
        if passed == len(results):
            print("\n🎉 Database is healthy!")
        else:
            print("\n🔧 Database needs attention. Review the issues above.")
        
        return passed == len(results)

def main():
    checker = DatabaseHealthChecker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'connection':
            checker.check_database_connection()
        elif command == 'performance':
            checker.check_database_performance()
        elif command == 'integrity':
            checker.check_database_integrity()
        elif command == 'consistency':
            checker.check_data_consistency()
        elif command == 'migrations':
            checker.check_migrations()
        elif command == 'size':
            checker.check_database_size()
        else:
            print("Unknown command. Use: connection, performance, integrity, consistency, migrations, size, or all")
    else:
        # Run comprehensive check
        checker.run_comprehensive_check()

if __name__ == "__main__":
    main() 