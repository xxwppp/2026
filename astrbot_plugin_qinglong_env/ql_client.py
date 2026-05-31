import httpx
from typing import List, Dict, Optional


class QinglongClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.token: Optional[str] = None
        self._client = httpx.AsyncClient(timeout=10)

    async def close(self):
        await self._client.aclose()

    async def _get_token(self) -> Optional[str]:
        if self.token:
            return self.token
        try:
            resp = await self._client.get(
                f"{self.base_url}/open/auth/token",
                params={"client_id": self.client_id, "client_secret": self.client_secret},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == 200:
                    self.token = data["data"]["token"]
                    return self.token
        except Exception:
            pass
        return None

    async def _request(self, method: str, path: str, **kwargs):
        token = await self._get_token()
        if not token:
            return None
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        for attempt in range(2):
            try:
                resp = await self._client.request(
                    method, f"{self.base_url}{path}", headers=headers, **kwargs
                )
                if resp.status_code == 401 and attempt == 0:
                    self.token = None
                    token = await self._get_token()
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                        continue
                return resp
            except httpx.TimeoutException:
                if attempt == 0:
                    continue
                return None
            except Exception:
                return None
        return None

    async def get_envs(self, search_value: str = None) -> List[Dict]:
        params = {}
        if search_value:
            params["searchValue"] = search_value
        resp = await self._request("GET", "/open/envs", params=params)
        if resp and resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    async def create_env(self, name: str, value: str, remarks: str = "") -> bool:
        resp = await self._request(
            "POST",
            "/open/envs",
            json=[{"name": name, "value": value, "remarks": remarks}],
        )
        return resp is not None and resp.status_code == 200

    async def update_env(self, env_id: int, name: str, value: str, remarks: str = "") -> bool:
        resp = await self._request(
            "PUT",
            "/open/envs",
            json={"id": env_id, "name": name, "value": value, "remarks": remarks},
        )
        return resp is not None and resp.status_code == 200

    async def delete_envs(self, env_ids: List[int]) -> bool:
        resp = await self._request("DELETE", "/open/envs", json=env_ids)
        return resp is not None and resp.status_code == 200

    async def delete_envs_by_name(self, name: str) -> bool:
        envs = await self.get_envs(name)
        if not envs:
            return True
        env_ids = [e["id"] for e in envs if e.get("name") == name]
        if not env_ids:
            return True
        return await self.delete_envs(env_ids)

    async def create_or_update_script(self, filename: str, content: str) -> bool:
        resp = await self._request(
            "PUT",
            "/open/scripts",
            json={"filename": filename, "content": content},
        )
        return resp is not None and resp.status_code in (200, 201)

    async def list_subscriptions(self, search: str = "") -> List[Dict]:
        params = {}
        if search:
            params["searchValue"] = search
        resp = await self._request("GET", "/open/subscriptions", params=params)
        if resp and resp.status_code == 200:
            return resp.json().get("data", [])
        return []

    async def run_subscription(self, sub_id: int) -> bool:
        resp = await self._request(
            "PUT", "/open/subscriptions/run", json=[sub_id]
        )
        return resp is not None and resp.status_code in (200, 201)
