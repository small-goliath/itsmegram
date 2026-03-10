#!/bin/bash
# rollback.sh - 배포 실패 시 롤백 스크립트

set -e

echo "=========================================="
echo "itsmegram v2.0 Rollback Script"
echo "=========================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Warning: This will rollback to the Instaloader version${NC}"
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 1
fi

echo ""
echo "Step 1/4: Rolling back code changes..."
if git checkout HEAD~15 -- backend/ 2>/dev/null; then
    echo -e "${GREEN}✓ Code rollback completed${NC}"
else
    echo -e "${RED}✗ Code rollback failed${NC}"
    exit 1
fi

echo ""
echo "Step 2/4: Restoring dependencies..."
cd backend

# Reinstall instaloader
if pip install instaloader==4.14 --quiet; then
    echo -e "${GREEN}✓ Instaloader installed${NC}"
else
    echo -e "${RED}✗ Instaloader installation failed${NC}"
    exit 1
fi

# Remove curl_cffi
if pip uninstall curl_cffi -y --quiet 2>/dev/null; then
    echo -e "${GREEN}✓ curl_cffi removed${NC}"
fi

# Reinstall requirements
if pip install -r requirements.txt --quiet; then
    echo -e "${GREEN}✓ Dependencies restored${NC}"
else
    echo -e "${RED}✗ Dependencies restoration failed${NC}"
    exit 1
fi

echo ""
echo "Step 3/4: Running tests..."
if python -m pytest tests/ -x -q 2>/dev/null || python3 -m pytest tests/ -x -q 2>/dev/null; then
    echo -e "${GREEN}✓ Tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Some tests failed (continuing anyway)${NC}"
fi

echo ""
echo "Step 4/4: Restarting service..."
if command -v systemctl &> /dev/null; then
    if sudo systemctl restart itsmegram 2>/dev/null; then
        echo -e "${GREEN}✓ Service restarted${NC}"
    else
        echo -e "${YELLOW}⚠ Service restart failed (you may need to restart manually)${NC}"
    fi
elif command -v docker &> /dev/null; then
    if docker-compose restart backend 2>/dev/null; then
        echo -e "${GREEN}✓ Docker containers restarted${NC}"
    else
        echo -e "${YELLOW}⚠ Docker restart failed (you may need to restart manually)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Please restart the service manually${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Rollback completed!${NC}"
echo "=========================================="
echo ""
echo "Please verify the rollback:"
echo "1. Check service status: curl http://localhost:8000/api/v1/health"
echo "2. Check logs: tail -f logs/app.log"
echo "3. Run a test analysis"
echo ""
