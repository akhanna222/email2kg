from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Document, Transaction, Party, Email, EmailDocumentLink
from typing import Dict, List, Any, Optional


class GraphService:
    """Service for building knowledge graph data structure."""

    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id

    def build_knowledge_graph(self) -> Dict[str, Any]:
        """
        Build complete knowledge graph with nodes and links.

        Returns:
            Dictionary with nodes and links for graph visualization
        """
        nodes = []
        links = []
        node_map = {}  # Track node IDs to avoid duplicates

        # Add Party nodes (only those involved in user's transactions)
        if self.user_id:
            # Get parties connected to user's documents
            parties = self.db.query(Party).join(
                Transaction, Transaction.party_id == Party.id
            ).join(
                Document, Transaction.document_id == Document.id
            ).filter(
                Document.user_id == self.user_id
            ).distinct().all()
        else:
            parties = self.db.query(Party).all()

        for party in parties:
            node_id = f"party-{party.id}"
            nodes.append({
                "id": node_id,
                "name": party.name,
                "type": "party",
                "entity_type": party.party_type or "vendor",
                "metadata": party.metadata or {}
            })
            node_map[node_id] = party

        # Add Document nodes
        if self.user_id:
            documents = self.db.query(Document).filter(Document.user_id == self.user_id).all()
        else:
            documents = self.db.query(Document).all()

        for doc in documents:
            node_id = f"document-{doc.id}"
            nodes.append({
                "id": node_id,
                "name": doc.filename,
                "type": "document",
                "doc_type": doc.document_type.value if doc.document_type else "unknown",
                "status": doc.processing_status.value,
                "size": doc.file_size,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
            })
            node_map[node_id] = doc

        # Add Transaction nodes and links
        if self.user_id:
            transactions = self.db.query(Transaction).join(Document).filter(
                Document.user_id == self.user_id
            ).all()
        else:
            transactions = self.db.query(Transaction).all()

        for txn in transactions:
            node_id = f"transaction-{txn.id}"
            nodes.append({
                "id": node_id,
                "name": f"${txn.amount} - {txn.transaction_type}",
                "type": "transaction",
                "amount": txn.amount,
                "currency": txn.currency,
                "transaction_type": txn.transaction_type,
                "date": txn.transaction_date.isoformat() if txn.transaction_date else None
            })
            node_map[node_id] = txn

            # Link transaction to document
            if txn.document_id:
                links.append({
                    "source": f"document-{txn.document_id}",
                    "target": node_id,
                    "type": "has_transaction",
                    "label": "extracted from"
                })

            # Link transaction to party
            if txn.party_id:
                links.append({
                    "source": node_id,
                    "target": f"party-{txn.party_id}",
                    "type": "involves_party",
                    "label": "involves"
                })

        # Add Email nodes and links
        emails = self.db.query(Email).limit(50).all()  # Limit emails for performance
        for email in emails:
            node_id = f"email-{email.id}"
            nodes.append({
                "id": node_id,
                "name": email.subject or "No Subject",
                "type": "email",
                "sender": email.sender,
                "receiver": email.receiver,
                "timestamp": email.timestamp.isoformat() if email.timestamp else None
            })
            node_map[node_id] = email

            # Link email to documents (via email_document_links)
            email_doc_links = self.db.query(EmailDocumentLink).filter(
                EmailDocumentLink.email_id == email.id
            ).all()

            for link in email_doc_links:
                links.append({
                    "source": node_id,
                    "target": f"document-{link.document_id}",
                    "type": "has_attachment",
                    "label": "attached"
                })

        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_nodes": len(nodes),
                "total_links": len(links),
                "parties": len([n for n in nodes if n["type"] == "party"]),
                "documents": len([n for n in nodes if n["type"] == "document"]),
                "transactions": len([n for n in nodes if n["type"] == "transaction"]),
                "emails": len([n for n in nodes if n["type"] == "email"])
            }
        }

    def get_document_graph(self, document_id: int) -> Dict[str, Any]:
        """
        Get knowledge graph for a specific document and its relationships.

        Args:
            document_id: ID of the document

        Returns:
            Subgraph centered on the document
        """
        nodes = []
        links = []

        # Get the document (filtered by user if user_id is set)
        query = self.db.query(Document).filter(Document.id == document_id)
        if self.user_id:
            query = query.filter(Document.user_id == self.user_id)

        document = query.first()
        if not document:
            return {"nodes": [], "links": [], "stats": {}}

        # Add document node
        doc_node_id = f"document-{document.id}"
        nodes.append({
            "id": doc_node_id,
            "name": document.filename,
            "type": "document",
            "doc_type": document.document_type.value if document.document_type else "unknown",
            "status": document.processing_status.value
        })

        # Add related transactions
        transactions = self.db.query(Transaction).filter(
            Transaction.document_id == document_id
        ).all()

        for txn in transactions:
            txn_node_id = f"transaction-{txn.id}"
            nodes.append({
                "id": txn_node_id,
                "name": f"${txn.amount} - {txn.transaction_type}",
                "type": "transaction",
                "amount": txn.amount,
                "transaction_type": txn.transaction_type
            })

            links.append({
                "source": doc_node_id,
                "target": txn_node_id,
                "type": "has_transaction",
                "label": "extracted"
            })

            # Add related party
            if txn.party_id:
                party = self.db.query(Party).filter(Party.id == txn.party_id).first()
                if party:
                    party_node_id = f"party-{party.id}"
                    # Check if party node already added
                    if not any(n["id"] == party_node_id for n in nodes):
                        nodes.append({
                            "id": party_node_id,
                            "name": party.name,
                            "type": "party",
                            "entity_type": party.party_type or "vendor"
                        })

                    links.append({
                        "source": txn_node_id,
                        "target": party_node_id,
                        "type": "involves_party",
                        "label": "involves"
                    })

        # Add related emails
        email_links = self.db.query(EmailDocumentLink).filter(
            EmailDocumentLink.document_id == document_id
        ).all()

        for email_link in email_links:
            email = self.db.query(Email).filter(Email.id == email_link.email_id).first()
            if email:
                email_node_id = f"email-{email.id}"
                nodes.append({
                    "id": email_node_id,
                    "name": email.subject or "No Subject",
                    "type": "email",
                    "sender": email.sender
                })

                links.append({
                    "source": email_node_id,
                    "target": doc_node_id,
                    "type": "has_attachment",
                    "label": "attached"
                })

        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_nodes": len(nodes),
                "total_links": len(links)
            }
        }

    def get_party_graph(self, party_id: int) -> Dict[str, Any]:
        """
        Get knowledge graph for a specific party (vendor) and their transactions.

        Args:
            party_id: ID of the party

        Returns:
            Subgraph centered on the party
        """
        nodes = []
        links = []

        # Get the party
        party = self.db.query(Party).filter(Party.id == party_id).first()
        if not party:
            return {"nodes": [], "links": [], "stats": {}}

        # Add party node
        party_node_id = f"party-{party.id}"
        nodes.append({
            "id": party_node_id,
            "name": party.name,
            "type": "party",
            "entity_type": party.party_type or "vendor"
        })

        # Add related transactions (filtered by user if user_id is set)
        query = self.db.query(Transaction).filter(Transaction.party_id == party_id)
        if self.user_id:
            query = query.join(Document).filter(Document.user_id == self.user_id)

        transactions = query.all()

        for txn in transactions:
            txn_node_id = f"transaction-{txn.id}"
            nodes.append({
                "id": txn_node_id,
                "name": f"${txn.amount} - {txn.transaction_type}",
                "type": "transaction",
                "amount": txn.amount,
                "transaction_type": txn.transaction_type,
                "date": txn.transaction_date.isoformat() if txn.transaction_date else None
            })

            links.append({
                "source": party_node_id,
                "target": txn_node_id,
                "type": "has_transaction",
                "label": "transaction"
            })

            # Add related document
            if txn.document_id:
                document = self.db.query(Document).filter(
                    Document.id == txn.document_id
                ).first()
                if document:
                    doc_node_id = f"document-{document.id}"
                    # Check if document node already added
                    if not any(n["id"] == doc_node_id for n in nodes):
                        nodes.append({
                            "id": doc_node_id,
                            "name": document.filename,
                            "type": "document",
                            "doc_type": document.document_type.value if document.document_type else "unknown"
                        })

                    links.append({
                        "source": doc_node_id,
                        "target": txn_node_id,
                        "type": "extracted_from",
                        "label": "from"
                    })

        return {
            "nodes": nodes,
            "links": links,
            "stats": {
                "total_nodes": len(nodes),
                "total_links": len(links),
                "total_transactions": len(transactions),
                "total_amount": sum(t.amount for t in transactions)
            }
        }
