#!/usr/bin/env python3
"""Refresh materialized views for analytics.

This script refreshes all materialized views used by the analytics system.
Can be run manually or scheduled via cron/Celery beat.

Usage:
    python scripts/refresh_materialized_views.py
    python scripts/refresh_materialized_views.py --concurrent
    python scripts/refresh_materialized_views.py --view mv_sprint_stats_enriched
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_async_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of materialized views to refresh
MATERIALIZED_VIEWS = [
    "mv_sprint_stats_enriched",
    "mv_issue_comment_stats",
]


async def refresh_view(
    session: AsyncSession,
    view_name: str,
    concurrent: bool = False
) -> tuple[str, float, bool]:
    """Refresh a single materialized view.
    
    Args:
        session: Database session
        view_name: Name of materialized view to refresh
        concurrent: Whether to use CONCURRENTLY option
        
    Returns:
        Tuple of (view_name, duration_seconds, success)
    """
    start_time = datetime.utcnow()
    
    try:
        # Build refresh command
        refresh_cmd = f"REFRESH MATERIALIZED VIEW"
        if concurrent:
            refresh_cmd += " CONCURRENTLY"
        refresh_cmd += f" {view_name}"
        
        logger.info(f"Refreshing {view_name}...")
        
        # Execute refresh
        await session.execute(text(refresh_cmd))
        await session.commit()
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✓ Refreshed {view_name} in {duration:.2f}s")
        return view_name, duration, True
        
    except Exception as e:
        logger.error(f"✗ Failed to refresh {view_name}: {e}")
        await session.rollback()
        return view_name, 0.0, False


async def refresh_all_views(concurrent: bool = False) -> dict:
    """Refresh all materialized views.
    
    Args:
        concurrent: Whether to use CONCURRENTLY option
        
    Returns:
        Dictionary with refresh results
    """
    results = {
        "total_views": len(MATERIALIZED_VIEWS),
        "successful": 0,
        "failed": 0,
        "total_duration": 0.0,
        "views": []
    }
    
    async for session in get_async_session():
        for view_name in MATERIALIZED_VIEWS:
            view_name_str, duration, success = await refresh_view(
                session, view_name, concurrent
            )
            
            results["views"].append({
                "name": view_name_str,
                "duration": duration,
                "success": success
            })
            
            if success:
                results["successful"] += 1
                results["total_duration"] += duration
            else:
                results["failed"] += 1
    
    return results


async def get_view_stats(session: AsyncSession, view_name: str) -> dict:
    """Get statistics about a materialized view.
    
    Args:
        session: Database session
        view_name: Name of materialized view
        
    Returns:
        Dictionary with view statistics
    """
    try:
        # Get row count
        result = await session.execute(
            text(f"SELECT COUNT(*) FROM {view_name}")
        )
        row_count = result.scalar()
        
        # Get view size
        result = await session.execute(
            text(f"SELECT pg_size_pretty(pg_total_relation_size('{view_name}'))")
        )
        size = result.scalar()
        
        # Get last refresh time (if available)
        # Note: PostgreSQL doesn't track this by default, would need custom tracking
        
        return {
            "name": view_name,
            "row_count": row_count,
            "size": size,
        }
        
    except Exception as e:
        logger.error(f"Failed to get stats for {view_name}: {e}")
        return {
            "name": view_name,
            "error": str(e)
        }


async def show_view_stats() -> None:
    """Show statistics for all materialized views."""
    logger.info("Materialized View Statistics:")
    logger.info("=" * 60)
    
    async for session in get_async_session():
        for view_name in MATERIALIZED_VIEWS:
            stats = await get_view_stats(session, view_name)
            
            if "error" in stats:
                logger.error(f"{view_name}: Error - {stats['error']}")
            else:
                logger.info(
                    f"{view_name}: "
                    f"{stats['row_count']:,} rows, "
                    f"{stats['size']}"
                )


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Refresh materialized views for analytics"
    )
    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Use CONCURRENTLY option (allows reads during refresh)"
    )
    parser.add_argument(
        "--view",
        type=str,
        help="Refresh only specific view"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show view statistics instead of refreshing"
    )
    
    args = parser.parse_args()
    
    # Show stats mode
    if args.stats:
        await show_view_stats()
        return
    
    # Refresh specific view
    if args.view:
        if args.view not in MATERIALIZED_VIEWS:
            logger.error(f"Unknown view: {args.view}")
            logger.info(f"Available views: {', '.join(MATERIALIZED_VIEWS)}")
            sys.exit(1)
        
        async for session in get_async_session():
            view_name, duration, success = await refresh_view(
                session, args.view, args.concurrent
            )
            
            if success:
                logger.info(f"Successfully refreshed {view_name} in {duration:.2f}s")
                sys.exit(0)
            else:
                logger.error(f"Failed to refresh {view_name}")
                sys.exit(1)
    
    # Refresh all views
    logger.info(f"Refreshing {len(MATERIALIZED_VIEWS)} materialized views...")
    if args.concurrent:
        logger.info("Using CONCURRENTLY option")
    
    results = await refresh_all_views(args.concurrent)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Refresh Summary:")
    logger.info(f"  Total views: {results['total_views']}")
    logger.info(f"  Successful: {results['successful']}")
    logger.info(f"  Failed: {results['failed']}")
    logger.info(f"  Total duration: {results['total_duration']:.2f}s")
    
    # Exit with error if any failed
    if results['failed'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

