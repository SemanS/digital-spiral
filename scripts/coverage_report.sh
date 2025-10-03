#!/bin/bash
# Generate test coverage report for Digital Spiral

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📊 Generating Test Coverage Report"
echo "===================================="
echo ""

# Run tests with coverage
echo "Running tests with coverage..."
pytest tests/ \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --cov-report=json \
    -v

echo ""
echo "===================================="
echo -e "${GREEN}✓ Coverage report generated!${NC}"
echo ""
echo "Reports available:"
echo "  - HTML: htmlcov/index.html"
echo "  - JSON: coverage.json"
echo ""
echo "To view HTML report:"
echo "  open htmlcov/index.html"
echo ""

# Extract coverage percentage
if [ -f coverage.json ]; then
    coverage=$(python3 -c "import json; print(f\"{json.load(open('coverage.json'))['totals']['percent_covered']:.1f}\")")
    echo -e "Overall Coverage: ${GREEN}${coverage}%${NC}"
    
    # Check if coverage meets threshold
    threshold=80
    if (( $(echo "$coverage >= $threshold" | bc -l) )); then
        echo -e "${GREEN}✓ Coverage meets threshold (${threshold}%)${NC}"
    else
        echo -e "${YELLOW}⚠ Coverage below threshold (${threshold}%)${NC}"
    fi
fi

