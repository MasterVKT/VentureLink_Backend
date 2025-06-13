#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venture_link_project.settings')
django.setup()

from django.db import connection

def check_subscription_tables():
    """Vérifie les tables liées aux abonnements."""
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== TABLES CONTENANT 'subscription' ===")
    subscription_tables = [table[0] for table in tables if 'subscription' in table[0].lower()]
    for table in subscription_tables:
        print(f"- {table}")
    
    print("\n=== TABLES CONTENANT 'payment' ===")
    payment_tables = [table[0] for table in tables if 'payment' in table[0].lower()]
    for table in payment_tables:
        print(f"- {table}")
    
    return subscription_tables, payment_tables

if __name__ == "__main__":
    check_subscription_tables() 