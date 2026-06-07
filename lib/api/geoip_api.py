import asyncio
import aiohttp
import ipaddress

# https://ip-api.com/docs/api:json

geoip_url = "http://ip-api.com/json"


class GeoIPError(Exception):
    pass


class GeoIPWrongIPError(GeoIPError):
    def __init__(self, ip: str):
        self.ip = ip
        super().__init__(f"Wrong IP: {ip}.")


class GeoIPAPIError(GeoIPError):
    def __init__(self, status: str | int):
        self.status = status
        super().__init__(f"GeoIP API error: {status}.")


async def geoip(ip: str) -> dict:
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise GeoIPWrongIPError(ip)

    async with aiohttp.ClientSession() as session:
        async with session.get(f'{geoip_url}/{ip}') as rs:
            if rs.status != 200:
                raise GeoIPAPIError(rs.status)

            json = await rs.json()

            if json['status'] == "fail":
                raise GeoIPAPIError(json['message'])

            return json


async def main():
    info = await geoip("45.141.215.17")
    print(info)


if __name__ == '__main__':
    asyncio.run(main())
