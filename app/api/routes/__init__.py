from fastapi import APIRouter
from .balance import router as balance_router
from .invest import router as invest_router
from .pools import router as pools_router
from .referrals import router as referrals_router
from .reinvest import router as reinvest_router
from .user import router as user_router
from .withdraw import router as withdraw_router
from .auth import router as auth_router

router = APIRouter()

router.include_router(balance_router, prefix="/balance", tags=["Balance"])
router.include_router(invest_router, prefix="/invest", tags=["Invest"])
router.include_router(pools_router, prefix="/pools", tags=["Pools"])
router.include_router(referrals_router, prefix="/referrals", tags=["Referrals"])
router.include_router(reinvest_router, prefix="/reinvest", tags=["Reinvest"])
router.include_router(user_router, prefix="/user", tags=["User"])
router.include_router(withdraw_router, prefix="/withdraw", tags=["Withdraw"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])