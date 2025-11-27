from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models import Transaction, Party, Document, DocumentType
from datetime import datetime, timedelta
from typing import Dict, Any, List


class QueryService:
    """Service for answering predefined queries about the knowledge graph."""

    def __init__(self, db: Session):
        self.db = db

    def answer_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Answer a predefined query.

        Args:
            query_type: One of 'total_spend', 'top_vendors', 'invoices_above'
            params: Query parameters

        Returns:
            Query result dictionary
        """
        if query_type == "total_spend":
            return self._total_spend(params.get('months', 1))
        elif query_type == "top_vendors":
            return self._top_vendors(params.get('limit', 10))
        elif query_type == "invoices_above":
            return self._invoices_above(params.get('amount', 0))
        else:
            return {"error": "Unknown query type"}

    def _total_spend(self, months: int) -> Dict[str, Any]:
        """
        Calculate total spend for last X months.

        Args:
            months: Number of months

        Returns:
            Dictionary with total spend and breakdown
        """
        since_date = datetime.now() - timedelta(days=months * 30)

        # Get total
        total = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.transaction_date >= since_date
        ).scalar() or 0.0

        # Get breakdown by type
        by_type = self.db.query(
            Transaction.transaction_type,
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.transaction_date >= since_date
        ).group_by(
            Transaction.transaction_type
        ).all()

        # Get breakdown by month
        by_month = self.db.query(
            func.date_trunc('month', Transaction.transaction_date).label('month'),
            func.sum(Transaction.amount).label('total')
        ).filter(
            Transaction.transaction_date >= since_date
        ).group_by(
            'month'
        ).order_by(
            'month'
        ).all()

        return {
            "query": f"Total spend last {months} months",
            "total": round(total, 2),
            "currency": "USD",
            "period_start": since_date.isoformat(),
            "period_end": datetime.now().isoformat(),
            "breakdown_by_type": [
                {"type": t[0], "amount": round(t[1], 2)}
                for t in by_type
            ],
            "breakdown_by_month": [
                {"month": t[0].strftime('%Y-%m'), "amount": round(t[1], 2)}
                for t in by_month
            ]
        }

    def _top_vendors(self, limit: int) -> Dict[str, Any]:
        """
        Get top vendors by total amount.

        Args:
            limit: Number of vendors to return

        Returns:
            Dictionary with top vendors
        """
        results = self.db.query(
            Party.name,
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).join(
            Transaction, Transaction.party_id == Party.id
        ).group_by(
            Party.id, Party.name
        ).order_by(
            desc('total')
        ).limit(limit).all()

        vendors = [
            {
                "name": r[0],
                "total_amount": round(r[1], 2),
                "transaction_count": r[2]
            }
            for r in results
        ]

        return {
            "query": f"Top {limit} vendors by amount",
            "vendors": vendors
        }

    def _invoices_above(self, amount: float) -> Dict[str, Any]:
        """
        Find invoices/receipts above a certain amount.

        Args:
            amount: Minimum amount

        Returns:
            Dictionary with matching transactions
        """
        transactions = self.db.query(
            Transaction, Party, Document
        ).outerjoin(
            Party, Transaction.party_id == Party.id
        ).outerjoin(
            Document, Transaction.document_id == Document.id
        ).filter(
            Transaction.amount >= amount
        ).order_by(
            desc(Transaction.amount)
        ).all()

        results = []
        for txn, party, doc in transactions:
            results.append({
                "id": txn.id,
                "amount": round(txn.amount, 2),
                "currency": txn.currency,
                "date": txn.transaction_date.isoformat() if txn.transaction_date else None,
                "type": txn.transaction_type,
                "vendor": party.name if party else None,
                "document_id": doc.id if doc else None,
                "document_filename": doc.filename if doc else None
            })

        return {
            "query": f"Invoices/receipts above ${amount}",
            "count": len(results),
            "transactions": results
        }

    def get_transaction_filters(self) -> Dict[str, List]:
        """Get available filter values for the UI."""
        # Get unique vendors
        vendors = self.db.query(Party.name).distinct().all()

        # Get document types
        doc_types = self.db.query(Transaction.transaction_type).distinct().all()

        # Get date range
        date_range = self.db.query(
            func.min(Transaction.transaction_date).label('min_date'),
            func.max(Transaction.transaction_date).label('max_date')
        ).first()

        return {
            "vendors": [v[0] for v in vendors],
            "document_types": [d[0] for d in doc_types if d[0]],
            "date_range": {
                "min": date_range[0].isoformat() if date_range[0] else None,
                "max": date_range[1].isoformat() if date_range[1] else None
            }
        }
