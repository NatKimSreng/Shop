#!/usr/bin/env python3
"""
Script to migrate from SQLite to PostgreSQL
Run this script to transfer data from SQLite to PostgreSQL
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from django.conf import settings

def backup_sqlite_data():
    """Create a backup of SQLite data"""
    print("📦 Creating backup of SQLite data...")
    
    # Create backup directory
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Export data to JSON
    call_command('dumpdata', 
                '--exclude', 'contenttypes',
                '--exclude', 'auth.Permission',
                '--indent', '2',
                '--output', 'backup/sqlite_backup.json')
    
    print("✅ SQLite backup created: backup/sqlite_backup.json")

def setup_postgresql():
    """Set up PostgreSQL database"""
    print("🗄️ Setting up PostgreSQL database...")
    
    # Check if PostgreSQL is configured
    if not os.environ.get('DB_HOST'):
        print("❌ PostgreSQL not configured. Please set environment variables:")
        print("   DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        return False
    
    try:
        # Test PostgreSQL connection
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ PostgreSQL connected: {version[0]}")
        
        # Run migrations
        call_command('migrate')
        print("✅ Database migrations completed")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL setup failed: {e}")
        return False

def restore_data_to_postgresql():
    """Restore data from backup to PostgreSQL"""
    print("🔄 Restoring data to PostgreSQL...")
    
    backup_file = Path("backup/sqlite_backup.json")
    if not backup_file.exists():
        print("❌ Backup file not found. Please run backup first.")
        return False
    
    try:
        # Load data into PostgreSQL
        call_command('loaddata', 'backup/sqlite_backup.json')
        print("✅ Data restored to PostgreSQL")
        return True
        
    except Exception as e:
        print(f"❌ Data restoration failed: {e}")
        return False

def verify_migration():
    """Verify that migration was successful"""
    print("🔍 Verifying migration...")
    
    try:
        from store.models import Product
        from payment.models import Order
        
        product_count = Product.objects.count()
        order_count = Order.objects.count()
        
        print(f"✅ Migration verified:")
        print(f"   Products: {product_count}")
        print(f"   Orders: {order_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

def main():
    """Main migration process"""
    print("🚀 Starting SQLite to PostgreSQL Migration")
    print("=" * 50)
    
    # Step 1: Backup SQLite data
    backup_sqlite_data()
    
    # Step 2: Setup PostgreSQL
    if not setup_postgresql():
        print("❌ Migration failed at PostgreSQL setup")
        return
    
    # Step 3: Restore data
    if not restore_data_to_postgresql():
        print("❌ Migration failed at data restoration")
        return
    
    # Step 4: Verify migration
    if not verify_migration():
        print("❌ Migration verification failed")
        return
    
    print("\n🎉 Migration completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your environment variables to use PostgreSQL")
    print("2. Test the application functionality")
    print("3. Keep the SQLite backup for safety")
    print("4. Consider setting up Redis for session storage")

if __name__ == '__main__':
    main() 