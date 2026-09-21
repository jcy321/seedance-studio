#!/bin/bash
# Seedance Studio - Startup Script
# Opens both frontend and backend
cd "$(dirname "$0")/backend"
echo "================================================"
echo "  Seedance Studio - AI视频创作平台"
echo "================================================"
echo ""
echo "  后端API:  http://localhost:8000/api/v1"
echo "  前端页面: http://localhost:8000"
echo "  开发验证码: 000000"
echo "  测试账号: admin@seedance.io / admin123456"
echo ""
echo "================================================"
exec python3 -m poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
