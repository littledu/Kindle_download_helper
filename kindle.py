"""
Note some download code from: https://github.com/sghctoma/bOOkp
Great Thanks
"""

from http.cookies import SimpleCookie
import os
import re
import json
import urllib
import urllib3

import browsercookie
import requests
import argparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DEFAULT_OUT_DIR = "DOWNLOADS"

KINDLE_HEADER = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/1AE148",
}

KINDLE_URLS = {
    "cn": {
        "bookall": "https://www.amazon.cn/hz/mycd/myx#/home/content/booksAll",
        "download": "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/FSDownloadContent?type=EBOK&key={}&fsn={}&device_type={}&customerId={}&authPool=AmazonCN",
        "payload": "https://www.amazon.cn/hz/mycd/ajax",
    },
    "com": {
        "bookall": "https://www.amazon.cn/hz/mycd/myx#/home/content/booksAll",
        "download": "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/FSDownloadContent?type=EBOK&key={}&fsn={}&device_type={}&customerId={}",
        "payload": "https://www.amazon.com/hz/mycd/ajax",
    },
}


class Kindle:
    def __init__(
        self, csrf_token, domain="cn", out_dir=DEFAULT_OUT_DIR, cut_length=100
    ):
        self.session = self.make_session()
        self.urls = KINDLE_URLS[domain]
        self.csrf_token = csrf_token
        self.total_to_download = 0
        self.out_dir = out_dir
        self.cut_length = cut_length

    def set_cookie_from_string(self, cookie_string):
        cj = self._parse_kindle_cookie(cookie_string)
        self.set_cookie(cj)

    def set_cookie(self, cookiejar):
        if not cookiejar:
            raise Exception("Please make sure your amazon cookie is right")
        self.session.cookies = cookiejar

    @staticmethod
    def _parse_kindle_cookie(kindle_cookie):
        cookie = SimpleCookie()
        cookie.load(kindle_cookie)
        cookies_dict = {}
        cookiejar = None
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value
            cookiejar = requests.utils.cookiejar_from_dict(
                cookies_dict, cookiejar=None, overwrite=True
            )
        return cookiejar

    def _get_csrf_token(self):
        """
        TODO: I do not know why I have to get csrf token in the page not in this way
        maybe figure out why in the future
        """
        r = self.session.get(
            "https://www.amazon.cn/hz/mycd/digital-console/deviceprivacycentre"
        )
        match = re.search(r'var csrfToken = "(.*)";', r.text)
        if not match:
            raise Exception("There's not csrf token here, please check")
        return match.group(1)

    def get_devices(self):
        payload = {"param": {"GetDevices": {}}}
        r = self.session.post(
            self.urls["payload"],
            data={
                "data": json.dumps(payload),
                "csrfToken": self.csrf_token,
            },
        )
        devices = r.json()
        if devices.get("error"):
            raise Exception(
                f"Error: {devices.get('error')}, please visit {self.urls['bookall']} to revoke the csrftoken and cookie"
            )
        devices = r.json()["GetDevices"]["devices"]
        return [device for device in devices if "deviceSerialNumber" in device]

    def get_all_asins(self):
        """
        TODO: refactor this function
        """
        startIndex = 0
        batchSize = 100
        payload = {
            "param": {
                "OwnershipData": {
                    "sortOrder": "DESCENDING",
                    "sortIndex": "DATE",
                    "startIndex": startIndex,
                    "batchSize": batchSize,
                    "contentType": "Ebook",
                    "itemStatus": ["Active"],
                    "originType": ["Purchase"],
                }
            }
        }

        asins = []
        while True:
            r = self.session.post(
                self.urls["payload"],
                data={"data": json.dumps(payload), "csrfToken": self.csrf_token},
            )
            result = r.json()
            asins += [book["asin"] for book in result["OwnershipData"]["items"]]

            if result["OwnershipData"]["hasMoreItems"]:
                startIndex += batchSize
                payload["param"]["OwnershipData"]["startIndex"] = startIndex
            else:
                break
        return asins

    def make_session(self):
        session = requests.Session()
        session.headers.update(KINDLE_HEADER)
        return session

    def download_one_book(self, asin, device, index):
        try:
            download_url = self.urls["download"].format(
                asin,
                device["deviceSerialNumber"],
                device["deviceType"],
                device["customerId"],
            )
            r = self.session.get(download_url, verify=False, stream=True)
            name = re.findall(
                r"filename\*=UTF-8''(.+)", r.headers["Content-Disposition"]
            )[0]
            name = urllib.parse.unquote(name)
            name = re.sub(r'[\\/:*?"<>|]', "_", name)
            if len(name) > self.cut_length:
                name = name[: self.cut_length - 5] + name[-5:]
            total_size = r.headers["Content-length"]
            out = os.path.join(self.out_dir, name)
            print(
                f"({index}/{self.total_to_download})downloading {name} {total_size} bytes"
            )
            with open(out, "wb") as f:
                for chunk in r.iter_content(chunk_size=512):
                    f.write(chunk)
            print(f"{name} downloaded")
        except Exception as e:
            print(str(e))
            print(f"{asin} download failed")

    def download_books(self, start_index=0):
        # use default device
        device = self.get_devices()[0]
        asins = self.get_all_asins()
        self.total_to_download = len(asins) - 1
        if start_index:
            print(f"recover index downloading {start_index}/{self.total_to_download}")
        index = start_index
        for asin in asins[start_index:]:
            self.download_one_book(asin, device, index)
            index += 1

        print(
            "\n\nAll done!\nNow you can use apprenticeharper's DeDRM tools "
            "(https://github.com/apprenticeharper/DeDRM_tools)\n"
            "with the following serial number to remove DRM: "
            + device["deviceSerialNumber"]
        )
        with open(os.path.join(self.out_dir, "key.txt"), "w") as f:
            f.write(f"Key is: {device['deviceSerialNumber']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csrf_token", help="amazon or amazon cn csrf token")

    cookie_group = parser.add_mutually_exclusive_group()
    cookie_group.add_argument(
        "--cookie", dest="cookie", default="", help="amazon or amazon cn cookie"
    )
    cookie_group.add_argument(
        "--cookie-file", dest="cookie_file", default="", help="load cookie local file"
    )

    parser.add_argument(
        "--cn",
        dest="domain",
        action="store_const",
        const="cn",
        default="com",
        help="if your account is an amazon.cn account",
    )
    parser.add_argument(
        "--recover-index",
        dest="index",
        type=int,
        default=0,
        help="recover-index if download failed",
    )
    parser.add_argument(
        "--cut-length",
        dest="cut_length",
        type=int,
        default=100,
        help="recover-index if download failed",
    )
    parser.add_argument(
        "-o", "--outdir", default=DEFAULT_OUT_DIR, help="dwonload output dir"
    )

    options = parser.parse_args()

    if not os.path.exists(options.outdir):
        os.makedirs(options.outdir)
    kindle = Kindle(
        options.csrf_token, options.domain, options.outdir, options.cut_length
    )
    if options.cookie_file:
        with open(options.cookie_file, "r") as f:
            kindle.set_cookie_from_string(f.read())
    elif options.cookie:
        kindle.set_cookie_from_string(options.cookie)
    else:
        kindle.set_cookie(browsercookie.load())
    kindle.download_books(start_index=options.index)
