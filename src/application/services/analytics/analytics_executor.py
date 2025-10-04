"""Analytics Executor Service for executing analytics queries."""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.schemas.analytics_spec import AnalyticsSpec
from .query_builder import QueryBuilder


class AnalyticsExecutor:
    """Execute analytics queries and return results."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        """Initialize executor.
        
        Args:
            session: Database session
            tenant_id: Tenant ID for RLS
        """
        self.session = session
        self.tenant_id = tenant_id
        self.query_builder = QueryBuilder(tenant_id)
    
    async def execute_spec(self, spec: AnalyticsSpec) -> Dict[str, Any]:
        """Execute analytics spec and return results.
        
        Args:
            spec: Analytics specification
            
        Returns:
            Dictionary with results and metadata
        """
        # Build SQL query
        sql_query, params = self.query_builder.build_query(spec)
        
        # Execute query
        start_time = time.time()
        result = await self._execute_query(sql_query, params)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Format results
        return {
            "data": result["rows"],
            "metadata": {
                "row_count": result["row_count"],
                "execution_time_ms": execution_time_ms,
                "sql_query": sql_query,
                "spec": spec.model_dump(),
                "executed_at": datetime.utcnow().isoformat(),
            }
        }
    
    async def execute_metric(
        self,
        metric_name: str,
        parameters: Dict[str, Any],
        sql_template: str,
    ) -> Dict[str, Any]:
        """Execute a predefined metric query.
        
        Args:
            metric_name: Metric name
            parameters: Query parameters
            sql_template: SQL template
            
        Returns:
            Dictionary with results and metadata
        """
        # Add tenant_id to parameters
        params = {**parameters, "tenant_id": self.tenant_id}
        
        # Execute query
        start_time = time.time()
        result = await self._execute_query(sql_template, params)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Format results
        return {
            "data": result["rows"],
            "metadata": {
                "metric_name": metric_name,
                "row_count": result["row_count"],
                "execution_time_ms": execution_time_ms,
                "parameters": parameters,
                "executed_at": datetime.utcnow().isoformat(),
            }
        }
    
    async def execute_raw_sql(
        self,
        sql_query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute raw SQL query (with validation).
        
        Args:
            sql_query: SQL query
            parameters: Query parameters
            
        Returns:
            Dictionary with results and metadata
            
        Raises:
            ValueError: If query is not a SELECT statement
        """
        # Validate query is SELECT only
        if not self._is_safe_query(sql_query):
            raise ValueError("Only SELECT queries are allowed")
        
        # Add tenant_id to parameters
        params = {**(parameters or {}), "tenant_id": self.tenant_id}
        
        # Execute query
        start_time = time.time()
        result = await self._execute_query(sql_query, params)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Format results
        return {
            "data": result["rows"],
            "metadata": {
                "row_count": result["row_count"],
                "execution_time_ms": execution_time_ms,
                "executed_at": datetime.utcnow().isoformat(),
            }
        }
    
    async def _execute_query(
        self,
        sql_query: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute SQL query and return results.
        
        Args:
            sql_query: SQL query
            parameters: Query parameters
            
        Returns:
            Dictionary with rows and row_count
        """
        # Execute query
        result = await self.session.execute(
            text(sql_query),
            parameters
        )
        
        # Fetch all rows
        rows = result.fetchall()
        
        # Convert rows to dictionaries
        if rows:
            columns = result.keys()
            rows_dict = [dict(zip(columns, row)) for row in rows]
        else:
            rows_dict = []
        
        return {
            "rows": rows_dict,
            "row_count": len(rows_dict),
        }
    
    def _is_safe_query(self, sql_query: str) -> bool:
        """Check if query is safe (SELECT only).
        
        Args:
            sql_query: SQL query
            
        Returns:
            True if safe, False otherwise
        """
        # Remove comments and whitespace
        query = sql_query.strip().upper()
        
        # Remove SQL comments
        query = query.split("--")[0]  # Remove line comments
        query = query.split("/*")[0]  # Remove block comments
        
        # Check if starts with SELECT
        if not query.startswith("SELECT"):
            return False
        
        # Check for dangerous keywords
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
            "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXEC",
            "EXECUTE", "CALL", "MERGE", "REPLACE",
        ]
        
        for keyword in dangerous_keywords:
            if keyword in query:
                return False
        
        return True
    
    async def validate_query(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL query without executing it.
        
        Args:
            sql_query: SQL query
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            "is_valid": False,
            "is_safe": False,
            "errors": [],
            "warnings": [],
        }
        
        # Check if safe
        if not self._is_safe_query(sql_query):
            validation["errors"].append("Query is not safe (only SELECT allowed)")
            return validation
        
        validation["is_safe"] = True
        
        # Try to prepare query (EXPLAIN)
        try:
            explain_query = f"EXPLAIN {sql_query}"
            await self.session.execute(text(explain_query))
            validation["is_valid"] = True
        except Exception as e:
            validation["errors"].append(f"Query validation failed: {str(e)}")
        
        return validation
    
    async def get_query_plan(self, sql_query: str) -> Dict[str, Any]:
        """Get query execution plan.
        
        Args:
            sql_query: SQL query
            
        Returns:
            Dictionary with query plan
        """
        # Get EXPLAIN output
        explain_query = f"EXPLAIN (FORMAT JSON) {sql_query}"
        result = await self.session.execute(text(explain_query))
        
        plan = result.fetchone()
        
        return {
            "plan": plan[0] if plan else None,
            "query": sql_query,
        }
    
    async def estimate_query_cost(
        self,
        sql_query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Estimate query execution cost.
        
        Args:
            sql_query: SQL query
            parameters: Query parameters
            
        Returns:
            Dictionary with cost estimates
        """
        # Add tenant_id to parameters
        params = {**(parameters or {}), "tenant_id": self.tenant_id}
        
        # Get EXPLAIN output
        explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE false) {sql_query}"
        result = await self.session.execute(text(explain_query), params)
        
        plan = result.fetchone()
        
        if plan and plan[0]:
            plan_data = plan[0][0]["Plan"]
            return {
                "total_cost": plan_data.get("Total Cost"),
                "startup_cost": plan_data.get("Startup Cost"),
                "plan_rows": plan_data.get("Plan Rows"),
                "plan_width": plan_data.get("Plan Width"),
            }
        
        return {}

