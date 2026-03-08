from pydantic import BaseModel
from typing import Optional

class Tenant(BaseModel):
    tenant_id: str
    subscription_tier: str
    billing_info: Optional[str]
    created_at: str

class SubscriptionTier(BaseModel):
    name: str
    price_per_month: float
    max_clusters: int
    max_gpus: int
    history_days: int
    api_access: bool