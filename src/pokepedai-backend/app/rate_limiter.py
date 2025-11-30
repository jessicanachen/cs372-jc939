import logging
import time
from collections import defaultdict
from typing import Dict

from fastapi import HTTPException, Request

logger = logging.getLogger("pokepedia.rate_limiter")

request_counters: Dict[str, Dict[str, int]] = defaultdict(dict)

class RateLimiter:
    def __init__(self, requests_limit, time_window):
        """
        Initialize a new rate limiter, limited per ip addres for request_limit requests in time_window.
        """
        self.requests_limit = requests_limit
        self.time_window = time_window

    async def __call__(self, request: Request):
        """
        Request to api, check if violates rate limit, returns True if not raises error if does.
        """

        # get client ip address
        client_ip = (
            request.client.host if request.client and request.client.host else "unknown"
        )
        route_path = request.url.path

        # get time of call
        current_time = int(time.time())
        key = f"{client_ip}:{route_path}"

        # initialize/update counter
        if key not in request_counters:
            request_counters[key] = {"timestamp": current_time, "count": 1}
        else:
            ts = request_counters[key]["timestamp"]
            count = request_counters[key]["count"]

            # if window expires reset
            if current_time - ts > self.time_window:
                request_counters[key]["timestamp"] = current_time
                request_counters[key]["count"] = 1
            else:
                # violates limit
                if count >= self.requests_limit:
                    logger.warning(
                        "Rate limit exceeded for %s on %s (limit=%d in %ds)",
                        client_ip,
                        route_path,
                        self.requests_limit,
                        self.time_window,
                    )
                    raise HTTPException(
                        status_code=429,
                        detail="Too Many Requests",
                    )
                request_counters[key]["count"] = count + 1

        # clean up expired entries
        for k in list(request_counters.keys()):
            if current_time - request_counters[k]["timestamp"] > self.time_window:
                request_counters.pop(k, None)

        return True
