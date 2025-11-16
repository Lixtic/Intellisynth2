"""
Firebase Firestore Service Layer
Provides base CRUD operations and database abstraction for Firestore
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter, Query
from app.firebase_config import get_firestore_db, firestore_doc_to_dict, firestore_docs_to_list

T = TypeVar('T')


class FirestoreService(Generic[T]):
    """Base service for Firestore operations"""
    
    def __init__(self, collection_name: str):
        """
        Initialize Firestore service
        
        Args:
            collection_name: Name of the Firestore collection
        """
        self.collection_name = collection_name
        self._db = None
    
    @property
    def db(self):
        """Get Firestore database instance (lazy initialization)"""
        if self._db is None:
            self._db = get_firestore_db()
        return self._db
    
    @property
    def collection(self):
        """Get Firestore collection reference"""
        return self.db.collection(self.collection_name)
    
    # CRUD Operations
    
    async def create(self, doc_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a document in Firestore
        
        Args:
            doc_id: Document ID (if None, Firestore auto-generates)
            data: Document data
            
        Returns:
            Created document with ID
        """
        # Add timestamps
        now = datetime.utcnow().isoformat()
        data['created_at'] = now
        data['updated_at'] = now
        
        if doc_id:
            # Use specified document ID
            doc_ref = self.collection.document(doc_id)
            doc_ref.set(data)
            data['id'] = doc_id
        else:
            # Auto-generate document ID
            doc_ref = self.collection.document()
            doc_ref.set(data)
            data['id'] = doc_ref.id
        
        return data
    
    async def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        doc_ref = self.collection.document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        return firestore_doc_to_dict(doc)
    
    async def get_all(
        self, 
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all documents with optional filtering, ordering, and pagination
        
        Args:
            filters: List of (field, operator, value) tuples for filtering
            order_by: Field to order by (prefix with '-' for descending)
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of documents
        """
        query: Query = self.collection
        
        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))
        
        # Apply ordering
        if order_by:
            if order_by.startswith('-'):
                # Descending order
                field = order_by[1:]
                query = query.order_by(field, direction=firestore.Query.DESCENDING)
            else:
                # Ascending order
                query = query.order_by(order_by)
        
        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        # Execute query
        docs = query.stream()
        return firestore_docs_to_list(docs)
    
    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a document
        
        Args:
            doc_id: Document ID
            data: Fields to update
            
        Returns:
            Updated document or None if not found
        """
        doc_ref = self.collection.document(doc_id)
        
        # Check if document exists
        if not doc_ref.get().exists:
            return None
        
        # Add update timestamp
        data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update document
        doc_ref.update(data)
        
        # Return updated document
        return await self.get(doc_id)
    
    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = self.collection.document(doc_id)
        
        # Check if document exists
        if not doc_ref.get().exists:
            return False
        
        # Delete document
        doc_ref.delete()
        return True
    
    async def exists(self, doc_id: str) -> bool:
        """
        Check if a document exists
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if exists, False otherwise
        """
        doc_ref = self.collection.document(doc_id)
        return doc_ref.get().exists
    
    async def count(self, filters: Optional[List[tuple]] = None) -> int:
        """
        Count documents with optional filtering
        
        Args:
            filters: List of (field, operator, value) tuples for filtering
            
        Returns:
            Number of documents matching filters
        """
        query = self.collection
        
        # Apply filters
        if filters:
            for field, operator, value in filters:
                query = query.where(filter=FieldFilter(field, operator, value))
        
        # Get count using aggregation query
        aggregation_query = query.count()
        result = aggregation_query.get()
        
        # Access the count value from the aggregation result
        for aggregation_result in result:
            return aggregation_result[0].value
        
        return 0
    
    # Batch Operations
    
    async def batch_create(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple documents in a batch
        
        Args:
            documents: List of document data dictionaries
            
        Returns:
            List of created documents with IDs
        """
        batch = self.db.batch()
        created_docs = []
        
        now = datetime.utcnow().isoformat()
        
        for doc_data in documents:
            doc_ref = self.collection.document()
            doc_data['id'] = doc_ref.id
            doc_data['created_at'] = now
            doc_data['updated_at'] = now
            
            batch.set(doc_ref, doc_data)
            created_docs.append(doc_data)
        
        # Commit batch
        batch.commit()
        
        return created_docs
    
    async def batch_update(self, updates: List[tuple]) -> List[Dict[str, Any]]:
        """
        Update multiple documents in a batch
        
        Args:
            updates: List of (doc_id, data) tuples
            
        Returns:
            List of updated documents
        """
        batch = self.db.batch()
        now = datetime.utcnow().isoformat()
        
        for doc_id, data in updates:
            doc_ref = self.collection.document(doc_id)
            data['updated_at'] = now
            batch.update(doc_ref, data)
        
        # Commit batch
        batch.commit()
        
        # Return updated documents
        return [await self.get(doc_id) for doc_id, _ in updates]
    
    async def batch_delete(self, doc_ids: List[str]) -> int:
        """
        Delete multiple documents in a batch
        
        Args:
            doc_ids: List of document IDs
            
        Returns:
            Number of documents deleted
        """
        batch = self.db.batch()
        
        for doc_id in doc_ids:
            doc_ref = self.collection.document(doc_id)
            batch.delete(doc_ref)
        
        # Commit batch
        batch.commit()
        
        return len(doc_ids)
    
    # Query Helpers
    
    async def find_one(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Find one document by field value
        
        Args:
            field: Field name
            value: Field value
            
        Returns:
            First matching document or None
        """
        docs = await self.get_all(filters=[(field, '==', value)], limit=1)
        return docs[0] if docs else None
    
    async def search(
        self,
        field: str,
        search_term: str,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search documents by partial text match
        
        Note: Firestore doesn't support full-text search natively.
        This uses range queries for prefix matching.
        For production, consider Algolia or Elasticsearch.
        
        Args:
            field: Field to search in
            search_term: Search term
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of matching documents
        """
        if not case_sensitive:
            search_term = search_term.lower()
        
        # Firestore range query for prefix matching
        # Note: This only works for exact prefix matches
        query = self.collection.where(
            filter=FieldFilter(field, '>=', search_term)
        ).where(
            filter=FieldFilter(field, '<=', search_term + '\uf8ff')
        )
        
        docs = query.stream()
        return firestore_docs_to_list(docs)
