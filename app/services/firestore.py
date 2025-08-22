from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter, Query

from app.core.logging import get_logger, log_firebase_operation
from app.services.firebase import get_firebase_app

logger = get_logger(__name__)


class FirestoreService:
    """Service for Firestore operations."""

    def __init__(self):
        self._client: Optional[firestore.Client] = None

    @property
    def client(self) -> firestore.Client:
        """Get Firestore client."""
        if self._client is None:
            self._client = firestore.client(app=get_firebase_app())
        return self._client

    async def create_document(
        self,
        collection: str,
        document_id: Optional[str] = None,
        data: Dict[str, Any] = None,
        merge: bool = False,
    ) -> str:
        """Create a document in Firestore."""
        try:
            if data is None:
                data = {}

            # Add timestamp fields
            now = firestore.SERVER_TIMESTAMP
            data.update(
                {
                    "created_at": now,
                    "updated_at": now,
                }
            )

            if document_id:
                doc_ref = self.client.collection(collection).document(document_id)
                doc_ref.set(data, merge=merge)
                result_id = document_id
            else:
                doc_ref = self.client.collection(collection).add(data)[1]
                result_id = doc_ref.id

            log_firebase_operation(
                "create_document",
                collection=collection,
                document_id=result_id,
                merge=merge,
            )

            return result_id

        except Exception as e:
            logger.error(
                "Failed to create document",
                collection=collection,
                document_id=document_id,
                error=str(e),
                exc_info=e,
            )
            raise

    async def get_document(
        self, collection: str, document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a document from Firestore."""
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc = doc_ref.get()

            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id

                log_firebase_operation(
                    "get_document",
                    collection=collection,
                    document_id=document_id,
                    found=True,
                )

                return data
            else:
                log_firebase_operation(
                    "get_document",
                    collection=collection,
                    document_id=document_id,
                    found=False,
                )
                return None

        except Exception as e:
            logger.error(
                "Failed to get document",
                collection=collection,
                document_id=document_id,
                error=str(e),
                exc_info=e,
            )
            raise

    async def update_document(
        self,
        collection: str,
        document_id: str,
        data: Dict[str, Any],
        merge: bool = False,
    ) -> bool:
        """Update a document in Firestore."""
        try:
            # Add updated timestamp
            data["updated_at"] = firestore.SERVER_TIMESTAMP

            doc_ref = self.client.collection(collection).document(document_id)

            if merge:
                doc_ref.set(data, merge=True)
            else:
                doc_ref.update(data)

            log_firebase_operation(
                "update_document",
                collection=collection,
                document_id=document_id,
                merge=merge,
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to update document",
                collection=collection,
                document_id=document_id,
                error=str(e),
                exc_info=e,
            )
            raise

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from Firestore."""
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc_ref.delete()

            log_firebase_operation(
                "delete_document", collection=collection, document_id=document_id
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to delete document",
                collection=collection,
                document_id=document_id,
                error=str(e),
                exc_info=e,
            )
            raise

    async def query_documents(
        self,
        collection: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        descending: bool = False,
    ) -> List[Dict[str, Any]]:
        """Query documents from Firestore."""
        try:
            query = self.client.collection(collection)

            # Apply filters
            if filters:
                for filter_item in filters:
                    field = filter_item["field"]
                    operator = filter_item["operator"]
                    value = filter_item["value"]
                    query = query.where(field, operator, value)

            # Apply ordering
            if order_by:
                direction = Query.DESCENDING if descending else Query.ASCENDING
                query = query.order_by(order_by, direction=direction)

            # Apply limit and offset
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            # Execute query
            docs = query.stream()

            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)

            log_firebase_operation(
                "query_documents",
                collection=collection,
                filters=filters,
                order_by=order_by,
                limit=limit,
                count=len(results),
            )

            return results

        except Exception as e:
            logger.error(
                "Failed to query documents",
                collection=collection,
                filters=filters,
                error=str(e),
                exc_info=e,
            )
            raise

    async def batch_write(self, operations: List[Dict[str, Any]]) -> bool:
        """Perform batch write operations."""
        try:
            batch = self.client.batch()

            for operation in operations:
                op_type = operation["type"]
                collection = operation["collection"]
                document_id = operation.get("document_id")
                data = operation.get("data", {})

                if op_type == "create":
                    if "created_at" not in data:
                        data["created_at"] = firestore.SERVER_TIMESTAMP
                    data["updated_at"] = firestore.SERVER_TIMESTAMP

                    if document_id:
                        doc_ref = self.client.collection(collection).document(
                            document_id
                        )
                        batch.set(doc_ref, data)
                    else:
                        doc_ref = self.client.collection(collection).document()
                        batch.set(doc_ref, data)

                elif op_type == "update":
                    data["updated_at"] = firestore.SERVER_TIMESTAMP
                    doc_ref = self.client.collection(collection).document(document_id)
                    batch.update(doc_ref, data)

                elif op_type == "delete":
                    doc_ref = self.client.collection(collection).document(document_id)
                    batch.delete(doc_ref)

            # Commit batch
            batch.commit()

            log_firebase_operation("batch_write", operations_count=len(operations))

            return True

        except Exception as e:
            logger.error(
                "Failed to execute batch write",
                operations_count=len(operations),
                error=str(e),
                exc_info=e,
            )
            raise

    async def run_transaction(self, transaction_func, *args, **kwargs) -> Any:
        """Run a Firestore transaction."""
        try:

            @firestore.transactional
            def transaction(transaction):
                return transaction_func(transaction, *args, **kwargs)

            result = transaction(self.client.transaction())

            log_firebase_operation("run_transaction")

            return result

        except Exception as e:
            logger.error("Failed to run transaction", error=str(e), exc_info=e)
            raise

    async def get_collection_count(
        self, collection: str, filters: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """Get count of documents in a collection."""
        try:
            query = self.client.collection(collection)

            # Apply filters
            if filters:
                for filter_item in filters:
                    field = filter_item["field"]
                    operator = filter_item["operator"]
                    value = filter_item["value"]
                    query = query.where(field, operator, value)

            # Get count
            count_query = query.count()
            result = count_query.get()
            count = result[0][0].value

            log_firebase_operation(
                "get_collection_count",
                collection=collection,
                filters=filters,
                count=count,
            )

            return count

        except Exception as e:
            logger.error(
                "Failed to get collection count",
                collection=collection,
                filters=filters,
                error=str(e),
                exc_info=e,
            )
            raise


# Global Firestore service instance
firestore_service = FirestoreService()


def get_firestore_service() -> FirestoreService:
    """Get the Firestore service instance."""
    return firestore_service
