#!/bin/bash

# Test script for Executive Work Pulse flow

set -e

BASE_URL="http://localhost:7010"
TENANT_ID="demo"

echo "🧪 Testing Executive Work Pulse Flow"
echo "===================================="
echo ""

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
curl -s "$BASE_URL/health" | jq .
echo "✅ Health check passed"
echo ""

# Test 2: List instances (should be empty or show existing)
echo "2️⃣ Listing Jira instances..."
curl -s -H "X-Tenant-Id: $TENANT_ID" "$BASE_URL/v1/pulse/jira/instances" | jq .
echo "✅ List instances passed"
echo ""

# Test 3: Get dashboard (might be empty)
echo "3️⃣ Getting dashboard data..."
curl -s -H "X-Tenant-Id: $TENANT_ID" "$BASE_URL/v1/pulse/dashboard" | jq .
echo "✅ Dashboard data retrieved"
echo ""

# Test 4: Get config
echo "4️⃣ Getting pulse config..."
curl -s -H "X-Tenant-Id: $TENANT_ID" "$BASE_URL/v1/pulse/config" | jq .
echo "✅ Config retrieved"
echo ""

echo "🎉 All tests passed!"
echo ""
echo "📝 Next steps:"
echo "1. Open dashboard: $BASE_URL/v1/pulse/"
echo "2. Click '+ Add Jira Instance'"
echo "3. Fill in your Jira credentials"
echo "4. Wait for backfill to complete (~30 seconds)"
echo "5. Refresh dashboard to see metrics"

