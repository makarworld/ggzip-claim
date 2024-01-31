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
            f.write("\n".join([x for x in data if x]) + "\n")

class GGZip:
    def __init__(self):
        self.session = tls_client.Session(
            client_identifier = "chrome_117",
            random_tls_extension_order = True
        )
    
    def get_user(self, wallet: str, proxy: Optional[str] = None) -> dict:
        return self.session.get(f"https://gg.zip/api/users/{wallet}", proxy = proxy).json()
    
    def get_invites(self, wallet: str, proxy: Optional[str] = None) -> dict:
        return self.session.get(f"https://gg.zip/api/invites/{wallet}", proxy = proxy).json()

    def claim(self, wallet: str, name: str, code: str, proxy: Optional[str] = None) -> Dict[str, bool]:
        return self.session.post(
            "https://gg.zip/api/claim",
            json = {
                "code": code.upper(),
                "username": name,
                "image": "https://gg.zip/assets/graphics/koji.png",
                "twitterId": str(randint(100000, 999999)),
                "wallet": wallet
            }, proxy = proxy).json()
    
def main():
    wallets = get_txt("wallets.txt")
    codes = get_txt("codes.txt")
    proxies = get_txt("proxies.txt")
    proxies = ["http://" + x if not x.startswith("http://") else x for x in proxies]
    
    if not wallets:
        logger.error("wallets.txt file is empty. Exiting...")
        input()
        exit()

    if not codes:
        logger.error("codes.txt file is empty. Exiting...")
        input()
        exit()

    logger.info(f"Load {len(wallets)} wallets and {len(codes)} codes")

    code_index = 0

    for wallet in wallets:
        used = get_txt("used.txt", raw=True)

        ggzip_sdk = GGZip()

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

        code = codes[code_index]
        code_index += 1
        while code in used:
            code = codes[code_index]
            if len(codes) == 0:
                logger.error("No codes left. Fill codes.txt file. Exiting...")
                input()
                exit()
            code_index += 1
        
        if proxies:
            proxy = proxies[randint(0, len(proxies)-1)]
            if MANY_PROXY_USES is False:
                proxies.pop(proxies.index(proxy))

            while proxy in used:
                proxy = proxies[randint(0, len(proxies)-1)]
                if MANY_PROXY_USES is False:
                    proxies.pop(proxies.index(proxy))

                if len(proxies) == 0:
                    logger.warning("No proxies left. Next accounts will be claimed without proxy.")
                    proxy = None
                    break
        else:
            proxy = None

        logger.debug(f"Claiming {wallet} as name @{name} with code {code} and proxy {proxy}")

        req = ggzip_sdk.claim(wallet, name, code, proxy = proxy)
        if req["success"]:
            info = ggzip_sdk.get_user(wallet, proxy = proxy)
            points = info["points"]
            logger.success(f"Claimed {wallet} as name @{name} with code {code} | POINTS: {points}")

            if points > 0:
                write_txt("success.txt", f"{wallet}:{points}")
            
            if APPEND_CODES:
                invites_list = ggzip_sdk.get_invites(wallet, proxy = proxy)
                invites = [invite["code"] for invite in invites_list]
                codes += invites
                write_txt("codes.txt", invites)
        else:
            info = ggzip_sdk.get_user(wallet, proxy = proxy)
            if info.get("success") is not False:
                points = info["points"]
                logger.success(f"Failed to claim {wallet}. Already registered. | POINTS: {points}")
                if points > 0:
                    write_txt("success.txt", f"{wallet}:{points}")
            else:
                logger.error(f"Failed to claim {wallet} as name @{name} with code {code} | {req=}")
                if req.get("message") == "Could not find wallet points":
                    pass # will be saved as used
                else:
                    continue 
            
        write_txt("used.txt", [name, code, wallet, proxy if not MANY_PROXY_USES else ""])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        input("Critical error. Press enter to exit...")
