from random import randint, choices
from loguru import logger
from typing import *
import tls_client 
import os

logger.level("DEBUG", color='<magenta>')

APPEND_CODES = True

def random_name() -> str:
    return ''.join(choices('abcdefghijklmnopqrstuvwxyz', k=12))

def get_txt(filename: str, raw: bool = False) -> List[str]:
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            if raw:
                data = f.read()
            else:
                data = f.read().splitlines()
                data = [i.strip() for i in data if i.strip()]
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

        code = codes.pop(randint(0, len(codes)-1))
        while code in used:
            code = codes.pop(randint(0, len(codes)-1))

        logger.debug(f"Claiming {wallet} as name @{name} with code {code}")

        req = session.post(
            "https://gg.zip/api/claim",
            json = {
                "code": code.upper(),
                "username": name,
                "image": "https://gg.zip/assets/graphics/koji.png",
                "twitterId": str(randint(100000, 9999999)),
                "wallet": wallet
            })
        if req.status_code == 200 and req.json()["success"]:
            info = session.get(f"https://gg.zip/api/users/{wallet}").json()
            points = info["points"]
            logger.success(f"Claimed {wallet} as name @{name} with code {code} | POINTS: {info['points']}")

            if points > 0:
                write_txt("success.txt", f"{wallet}:{points}")
            
            if APPEND_CODES:
                invites_list = session.get(f"https://gg.zip/api/invites/{wallet}").json()
                invites = [invite["code"] for invite in invites_list]
                write_txt("codes.txt", invites)
        else:
            logger.error(f"Failed to claim {wallet} as name @{name} with code {code} | {req.status_code=}")

        write_txt("used.txt", [name, code, wallet])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)