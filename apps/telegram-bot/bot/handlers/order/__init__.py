from __future__ import annotations

from aiogram import Router

from .applicants import router as applicants_router
from .country_city import router as country_city_router
from .entry import router as entry_router
from .promo_payment import router as promo_payment_router
from .summary import router as summary_router

router = Router()
router.include_router(entry_router)
router.include_router(country_city_router)
router.include_router(applicants_router)
router.include_router(promo_payment_router)
router.include_router(summary_router)
