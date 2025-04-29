from fastapi import APIRouter, HTTPException
from backend.models.balance import TxLog
from backend.utils.mongo import db
from pymongo import ReturnDocument
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/balance/deduct")
async def deduct_balance(log: TxLog):
    total_cost = (log.rate_per_unit * log.units)
    logger.debug(f"Attempting to deduct {total_cost} Bunny Bits from organization '{log.organization}'.")

    # Atomically check the threshold and deduct if valid
    updated_org = db.organizations.find_one_and_update(
        {
            "organization_name": log.organization,
            "balance": {"$gte": total_cost}
        },
        {
            "$inc": { "balance": -total_cost }
        },
        return_document=ReturnDocument.AFTER
    )

    if not updated_org:
        logger.warning(f"Deduction failed for organization '{log.organization}'. Insufficient balance or organization not found.")
        raise HTTPException(status_code=402, detail="Insufficient Bunny Bits or organization not found")

    logger.info(f"Deducted {total_cost} Bunny Bits from organization '{log.organization}'.\n New balance: {updated_org['balance']}")
    return {
        "message": "Bunny Bits deducted successfully",
        "deducted": total_cost,
        "new_balance": updated_org["balance"]
    }
