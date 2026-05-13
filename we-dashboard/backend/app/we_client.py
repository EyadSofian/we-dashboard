"""
WE (Telecom Egypt) Quota Client.

Reverse-engineered from api-my.te.eg internal API used by my.te.eg portal.
4-step flow:
  1) querySysParams        -> establishes session cookies
  2) userAuthenticate      -> returns token, custName, subscriberId
  3) getSubscribedOfferings-> returns mainOfferingId
  4) queryFreeUnit         -> returns total/used/remain/effectiveTime/expireTime
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

BASE = "https://api-my.te.eg"
EP_SYS = f"{BASE}/echannel/service/besapp/base/rest/busiservice/v1/common/querySysParams"
EP_AUTH = f"{BASE}/echannel/service/besapp/base/rest/busiservice/v1/auth/userAuthenticate"
EP_OFFERINGS = f"{BASE}/echannel/service/besapp/base/rest/busiservice/cz/v1/auth/getSubscribedOfferings"
EP_QUOTA = f"{BASE}/echannel/service/besapp/base/rest/busiservice/cz/cbs/bb/queryFreeUnit"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def _common_headers(token: str = "") -> dict:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Content-Type": "application/json",
        "Origin": BASE,
        "Referer": f"{BASE}/echannel/",
        "User-Agent": USER_AGENT,
        "channelId": "702",
        "csrftoken": token,
        "delegatorSubsId": "",
        "isCoporate": "false",
        "isMobile": "false",
        "isSelfcare": "true",
        "languageCode": "en-US",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }


class WEAuthError(Exception):
    pass


class WEAPIError(Exception):
    def __init__(self, message: str, ret_code: Optional[str] = None, ret_msg: Optional[str] = None):
        super().__init__(message)
        self.ret_code = ret_code
        self.ret_msg = ret_msg


@dataclass
class QuotaSnapshot:
    customer_name: str
    offer_name: str
    total_gb: float
    used_gb: float
    remain_gb: float
    usage_pct: float
    effective_time_ms: int
    expire_time_ms: int


class WEClient:
    def __init__(self, landline: str, password: str, timeout: float = 20.0):
        if not landline or len(landline) < 4:
            raise ValueError("Invalid landline")
        self.landline = landline.strip()
        self.password = password
        # Account ID format: FBB + landline without leading zero (per reverse-engineered flow)
        self.acct_id = "FBB" + self.landline[1:]
        self.timeout = timeout

    async def fetch_quota(self) -> QuotaSnapshot:
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=False,
            http2=False,
        ) as client:
            # Step 1: bootstrap session cookies
            r1 = await client.post(EP_SYS, headers=_common_headers(), json={})
            r1.raise_for_status()

            # Step 2: authenticate
            auth_payload = {
                "acctId": self.acct_id,
                "appLocale": "en-US",
                "password": self.password,
            }
            r2 = await client.post(EP_AUTH, headers=_common_headers(), json=auth_payload)
            r2.raise_for_status()
            auth_data = r2.json()
            header = auth_data.get("header", {})
            if header.get("retCode") != "0":
                raise WEAuthError(
                    f"Auth failed: retCode={header.get('retCode')} msg={header.get('retMsg')}"
                )
            body = auth_data["body"]
            token = body["token"]
            sub_id = body["subscriber"]["subscriberId"]
            cust_name = body["customer"]["custName"]

            # Step 3: get subscribed offerings
            offers_payload = {
                "msisdn": self.acct_id,
                "numberServiceType": "FBB",
                "groupId": "",
            }
            r3 = await client.post(
                EP_OFFERINGS, headers=_common_headers(token=token), json=offers_payload
            )
            r3.raise_for_status()
            offers_data = r3.json()
            if offers_data.get("header", {}).get("retCode") != "0":
                raise WEAPIError(
                    "Failed to get offerings",
                    ret_code=offers_data.get("header", {}).get("retCode"),
                    ret_msg=offers_data.get("header", {}).get("retMsg"),
                )
            offering_list = offers_data["body"].get("offeringList", [])
            if not offering_list:
                raise WEAPIError("No offerings returned")
            main_offer_id = offering_list[0]["mainOfferingId"]

            # Step 4: query quota
            quota_payload = {"subscriberId": sub_id, "mainOfferId": main_offer_id}
            r4 = await client.post(
                EP_QUOTA, headers=_common_headers(token=token), json=quota_payload
            )
            r4.raise_for_status()
            quota_data = r4.json()
            if quota_data.get("header", {}).get("retCode") != "0":
                raise WEAPIError(
                    "Failed to query quota",
                    ret_code=quota_data.get("header", {}).get("retCode"),
                    ret_msg=quota_data.get("header", {}).get("retMsg"),
                )
            body_q = quota_data.get("body") or []
            if not body_q:
                raise WEAPIError("Empty quota body")
            q = body_q[0]
            total = float(q["total"])
            used = float(q["used"])
            remain = float(q["remain"])
            usage_pct = (used / total * 100.0) if total > 0 else 0.0
            return QuotaSnapshot(
                customer_name=cust_name,
                offer_name=q.get("offerName", ""),
                total_gb=total,
                used_gb=used,
                remain_gb=remain,
                usage_pct=usage_pct,
                effective_time_ms=int(q["effectiveTime"]),
                expire_time_ms=int(q["expireTime"]),
            )


async def fetch_with_retry(landline: str, password: str, retries: int = 2) -> QuotaSnapshot:
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            return await WEClient(landline, password).fetch_quota()
        except (httpx.HTTPError, WEAPIError) as e:
            last_exc = e
            logger.warning("WE fetch attempt %d failed: %s", attempt + 1, e)
            if attempt < retries:
                await asyncio.sleep(2 ** attempt)
        except WEAuthError:
            # Don't retry auth errors - credentials are wrong
            raise
    assert last_exc is not None
    raise last_exc
