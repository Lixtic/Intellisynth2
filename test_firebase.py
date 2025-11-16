"""
Test Firebase Connection
Tests the Firebase Admin SDK initialization and Firestore connection
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_firebase_connection():
    """Test Firebase connection and basic operations"""
    
    print("=" * 60)
    print("Firebase Connection Test")
    print("=" * 60)
    
    # Step 1: Check credentials file
    print("\n1. Checking Firebase credentials file...")
    creds_path = os.getenv('FIREBASE_CREDENTIALS', './intellisynth-c1050-firebase-adminsdk-fbsvc-61edd8337e.json')
    
    if os.path.exists(creds_path):
        print(f"   ✓ Credentials file found: {creds_path}")
    else:
        print(f"   ✗ Credentials file NOT found: {creds_path}")
        print("\n   Please download the service account key from:")
        print("   https://console.firebase.google.com/project/intellisynth-c1050/settings/serviceaccounts/adminsdk")
        return False
    
    # Step 2: Initialize Firebase
    print("\n2. Initializing Firebase Admin SDK...")
    try:
        from app.firebase_config import firebase_config
        
        result = firebase_config.initialize(creds_path)
        if result:
            print("   ✓ Firebase initialized successfully!")
        else:
            print("   ✗ Firebase initialization failed")
            return False
    except Exception as e:
        print(f"   ✗ Error initializing Firebase: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test Firestore connection
    print("\n3. Testing Firestore database connection...")
    try:
        from app.firebase_config import get_firestore_db
        
        db = get_firestore_db()
        print(f"   ✓ Firestore client created: {type(db).__name__}")
    except Exception as e:
        print(f"   ✗ Error connecting to Firestore: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Test basic Firestore operations
    print("\n4. Testing basic Firestore operations...")
    try:
        from google.cloud import firestore
        
        # Create a test collection reference
        test_collection = db.collection('_test_connection')
        
        # Try to write a test document
        test_doc = {
            'test': True,
            'message': 'Firebase connection test',
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        doc_ref = test_collection.document('connection_test')
        doc_ref.set(test_doc)
        print("   ✓ Test document written successfully")
        
        # Try to read the test document
        doc = doc_ref.get()
        if doc.exists:
            print("   ✓ Test document read successfully")
            data = doc.to_dict()
            print(f"   ✓ Document data: {data}")
        else:
            print("   ⚠ Test document was written but could not be read")
        
        # Clean up - delete test document
        doc_ref.delete()
        print("   ✓ Test document deleted (cleanup)")
        
    except Exception as e:
        print(f"   ✗ Error during Firestore operations: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if it's a permissions error
        error_str = str(e).lower()
        if 'permission' in error_str or 'forbidden' in error_str or '403' in error_str:
            print("\n   ⚠ This appears to be a permissions error.")
            print("   Please check Firestore security rules at:")
            print("   https://console.firebase.google.com/project/intellisynth-c1050/firestore/rules")
            print("\n   For testing, you can use these rules:")
            print("   rules_version = '2';")
            print("   service cloud.firestore {")
            print("     match /databases/{database}/documents {")
            print("       match /{document=**} {")
            print("         allow read, write: if true;  // Allow all for testing")
            print("       }")
            print("     }")
            print("   }")
        
        return False
    
    # Step 5: Test FirestoreService
    print("\n5. Testing FirestoreService class...")
    try:
        from app.services.firebase_service import FirestoreService
        
        # Create a test service
        test_service = FirestoreService('_test_service')
        print(f"   ✓ FirestoreService created for collection: {test_service.collection_name}")
        
        # Test async operations (run synchronously for testing)
        import asyncio
        
        async def test_crud():
            # Create
            doc_data = {'name': 'Test Item', 'value': 123}
            created = await test_service.create(doc_id='test_item_1', data=doc_data)
            print(f"   ✓ Created document: {created.get('id')}")
            
            # Read
            retrieved = await test_service.get('test_item_1')
            print(f"   ✓ Retrieved document: {retrieved.get('name')}")
            
            # Update
            updated = await test_service.update('test_item_1', {'value': 456})
            print(f"   ✓ Updated document: value={updated.get('value')}")
            
            # List
            all_docs = await test_service.get_all()
            print(f"   ✓ Listed documents: {len(all_docs)} found")
            
            # Delete
            deleted = await test_service.delete('test_item_1')
            print(f"   ✓ Deleted document: {deleted}")
            
            return True
        
        # Run async test
        result = asyncio.run(test_crud())
        if not result:
            return False
            
    except Exception as e:
        print(f"   ✗ Error testing FirestoreService: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Success!
    print("\n" + "=" * 60)
    print("✓ All Firebase connection tests passed!")
    print("=" * 60)
    print("\nYour Firebase setup is working correctly!")
    print("\nNext steps:")
    print("1. Review FIREBASE_INTEGRATION_STATUS.md for migration status")
    print("2. Continue with Agent model migration to Firestore")
    print("3. Update .env to set DATABASE_TYPE=firebase when ready")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = test_firebase_connection()
    sys.exit(0 if success else 1)
