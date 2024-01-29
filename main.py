from random import randint, choices
from loguru import logger
from typing import *
import tls_client 
import os

logger.level("DEBUG", color='<magenta>')

APPEND_CODES = True
MANY_PROXY_USES = False

def random_name() -> str:
    return ''.join(choices('abcdefghijklmnopqrstuvwxyz', k=12))

def get_txt(filename: str, raw: bool = False) -> List[str]:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            if raw:
                data = f.read()
            else:
                data = [line.strip() for line in f if line.strip()]
    else:
        logger.debug(f"File {filename} not found. It was created automatically.")
        open(filename, "w", encoding="utf-8").close()
        if raw:
            data = []
        else:
            data = ""

    return data 

def write_txt(filename: str, data: Union[List[str], str]) -> None:
    if not os.path.exists(filename):
        logger.debug(f"File {filename} not found. It was created automatically.")
        open(filename, "w", encoding="utf-8").close()
    
    with open(filename, "a", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data + "\n")
        else:
            f.write("\n".join(data) + "\n")

def main():
    wallets = get_txt("wallets.txt")
    codes = get_txt("codes.txt")
    proxies = get_txt("proxies.txt")
    
    if not wallets:
        logger.error("wallets.txt file is empty. Exiting...")
        input()
        exit()

    if not codes:
        logger.error("codes.txt file is empty. Exiting...")
        input()
        exit()

    logger.info(f"Load {len(wallets)} wallets and {len(codes)} codes")

    for wallet in wallets:
        used = get_txt("used.txt", raw=True)
        if APPEND_CODES:
            codes = get_txt("codes.txt")

        session = tls_client.Session(
            client_identifier = "chrome_117",
            random_tls_extension_order = True
        )
        if wallet in used:
            logger.debug(f"{wallet} already claimed. Skipping...")
            continue

        name = random_name()
        while name in used:
            name = random_name()

        if len(codes) == 0:
            logger.error("No codes left. Fill codes.txt file. Exiting...")
            input()
            exit()

        code = codes.pop(randint(0, len(codes)-1))
        while code in used:
            code = codes.pop(randint(0, len(codes)-1))
            if len(codes) == 0:
                logger.error("No codes left. Fill codes.txt file. Exiting...")
                input()
                exit()
        
        if proxies:
            proxy = proxies.pop(randint(0, len(proxies)-1))
            while proxy in used:
                proxy = proxies.pop(randint(0, len(proxies)-1))
                if len(proxies) == 0:
                    logger.warning("No proxies left. Next accounts will be claimed without proxy.")
                    proxy = None
                    break
        else:
            proxy = None

        logger.debug(f"Claiming {wallet} as name @{name} with code {code} and proxy {proxy}")

        req = session.post(
            "https://gg.zip/api/claim",
            json = {
                "code": code.upper(),
                "username": name,
                "image": "https://gg.zip/assets/graphics/koji.png",
                "twitterId": str(randint(100000, 9999999)),
                "wallet": wallet
            }, proxy = proxy)
        if req.status_code == 200 and req.json()["success"]:
            info = session.get(f"https://gg.zip/api/users/{wallet}", proxy = proxy).json()
            points = info["points"]
            logger.success(f"Claimed {wallet} as name @{name} with code {code} | POINTS: {info['points']}")

            if points > 0:
                write_txt("success.txt", f"{wallet}:{points}")
            
            if APPEND_CODES:
                invites_list = session.get(f"https://gg.zip/api/invites/{wallet}", proxy = proxy).json()
                invites = [invite["code"] for invite in invites_list]
                write_txt("codes.txt", invites)
        else:
            logger.error(f"Failed to claim {wallet} as name @{name} with code {code} | {req.status_code=}")

        write_txt("used.txt", [name, code, wallet, proxy if not MANY_PROXY_USES else ""])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        input("Critical error. Press enter to exit...")