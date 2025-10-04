#!/usr/bin/env python3
"""Seed metrics catalog with predefined metrics.

This script loads predefined metrics from Python module and inserts them
into the metrics_catalog table. Can be run multiple times (idempotent).

Usage:
    python scripts/seed_metrics_catalog.py
    python scripts/seed_metrics_catalog.py --tenant-id <uuid>
"""

import asyncio
import argparse
import logging
import sys
from pathlib import Path
from uuid import UUID, uuid4

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import get_async_session
from src.application.services.analytics import MetricsCatalogService
from src.domain.analytics.predefined_metrics import PREDEFINED_METRICS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def seed_metrics(tenant_id: UUID) -> dict:
    """Seed metrics catalog for a tenant.
    
    Args:
        tenant_id: Tenant ID
        
    Returns:
        Dictionary with seeding results
    """
    results = {
        "total": len(PREDEFINED_METRICS),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "metrics": []
    }
    
    async for session in get_async_session():
        service = MetricsCatalogService(session)
        
        for metric_def in PREDEFINED_METRICS:
            try:
                metric_name = metric_def["name"]
                logger.info(f"Processing metric: {metric_name}")
                
                # Check if metric exists
                existing = await service.get_metric(tenant_id, metric_name)
                
                if existing:
                    # Update existing metric
                    logger.info(f"  Updating existing metric: {metric_name}")
                    
                    updated = await service.update_metric(
                        tenant_id=tenant_id,
                        metric_name=metric_name,
                        display_name=metric_def["display_name"],
                        description=metric_def["description"],
                        category=metric_def["category"],
                        sql_template=metric_def["sql_template"],
                        aggregation=metric_def["aggregation"],
                        parameters=metric_def.get("parameters"),
                        unit=metric_def.get("unit"),
                        tags=metric_def.get("tags"),
                    )
                    
                    if updated:
                        results["updated"] += 1
                        results["metrics"].append({
                            "name": metric_name,
                            "action": "updated"
                        })
                        logger.info(f"  ✓ Updated: {metric_name}")
                    else:
                        results["errors"] += 1
                        logger.error(f"  ✗ Failed to update: {metric_name}")
                else:
                    # Create new metric
                    logger.info(f"  Creating new metric: {metric_name}")
                    
                    created = await service.create_metric(
                        tenant_id=tenant_id,
                        name=metric_def["name"],
                        display_name=metric_def["display_name"],
                        description=metric_def["description"],
                        category=metric_def["category"],
                        sql_template=metric_def["sql_template"],
                        aggregation=metric_def["aggregation"],
                        parameters=metric_def.get("parameters"),
                        unit=metric_def.get("unit"),
                        tags=metric_def.get("tags"),
                    )
                    
                    if created:
                        results["created"] += 1
                        results["metrics"].append({
                            "name": metric_name,
                            "action": "created"
                        })
                        logger.info(f"  ✓ Created: {metric_name}")
                    else:
                        results["errors"] += 1
                        logger.error(f"  ✗ Failed to create: {metric_name}")
                
            except Exception as e:
                results["errors"] += 1
                logger.error(f"  ✗ Error processing {metric_def['name']}: {e}")
        
        # Commit all changes
        await session.commit()
    
    return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed metrics catalog with predefined metrics"
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Tenant ID (UUID). If not provided, uses a default test tenant."
    )
    
    args = parser.parse_args()
    
    # Get or create tenant ID
    if args.tenant_id:
        try:
            tenant_id = UUID(args.tenant_id)
        except ValueError:
            logger.error(f"Invalid tenant ID: {args.tenant_id}")
            sys.exit(1)
    else:
        # Use default test tenant
        tenant_id = UUID("00000000-0000-0000-0000-000000000001")
        logger.info(f"Using default test tenant ID: {tenant_id}")
    
    logger.info(f"Seeding metrics catalog for tenant: {tenant_id}")
    logger.info(f"Total metrics to process: {len(PREDEFINED_METRICS)}")
    logger.info("=" * 60)
    
    # Seed metrics
    results = await seed_metrics(tenant_id)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Seeding Summary:")
    logger.info(f"  Total metrics: {results['total']}")
    logger.info(f"  Created: {results['created']}")
    logger.info(f"  Updated: {results['updated']}")
    logger.info(f"  Skipped: {results['skipped']}")
    logger.info(f"  Errors: {results['errors']}")
    
    if results['errors'] > 0:
        logger.error("Seeding completed with errors")
        sys.exit(1)
    else:
        logger.info("✓ Seeding completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

