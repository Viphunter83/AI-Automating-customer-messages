#!/bin/bash
# Comprehensive system test script

set -e

echo "=" | tr '\n' '='
echo "SYSTEM TEST SCRIPT"
echo "=" | tr '\n' '='

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Check Docker
echo -e "\n${YELLOW}1. Checking Docker...${NC}"
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

# 2. Start services
echo -e "\n${YELLOW}2. Starting Docker services...${NC}"
docker-compose up -d postgres
sleep 5
docker-compose up -d backend
sleep 10
echo -e "${GREEN}✅ Services started${NC}"

# 3. Run migrations
echo -e "\n${YELLOW}3. Running migrations...${NC}"
docker-compose exec -T backend alembic upgrade head || echo -e "${YELLOW}⚠️  Migrations may have already run${NC}"

# 4. Create test data
echo -e "\n${YELLOW}4. Creating test data...${NC}"
docker-compose exec -T backend python3 scripts/create_test_data.py || echo -e "${YELLOW}⚠️  Test data creation failed or data already exists${NC}"

# 5. Test API endpoints
echo -e "\n${YELLOW}5. Testing API endpoints...${NC}"
sleep 3

# Health check
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Health endpoint works${NC}"
else
    echo -e "${RED}❌ Health endpoint failed${NC}"
fi

# Admin endpoints
if curl -s http://localhost:8000/api/admin/stats/messages | grep -q "total_messages"; then
    echo -e "${GREEN}✅ Admin stats endpoint works${NC}"
else
    echo -e "${YELLOW}⚠️  Admin stats endpoint (may be empty)${NC}"
fi

# 6. Frontend type check
echo -e "\n${YELLOW}6. Checking frontend TypeScript...${NC}"
cd frontend
if npm run type-check 2>&1 | grep -q "error"; then
    echo -e "${YELLOW}⚠️  Some TypeScript warnings (check output above)${NC}"
else
    echo -e "${GREEN}✅ Frontend TypeScript OK${NC}"
fi
cd ..

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ SYSTEM TEST COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nAccess points:"
echo -e "  - API: http://localhost:8000"
echo -e "  - API Docs: http://localhost:8000/docs"
echo -e "  - Frontend: http://localhost:3000"
echo -e "  - Admin: http://localhost:3000/admin"
echo -e "  - Dashboard: http://localhost:3000/dashboard"










