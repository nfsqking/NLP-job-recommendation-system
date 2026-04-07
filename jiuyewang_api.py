import requests
import urllib3
import ssl

# 修复 SSL 不安全旧协议问题
class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # 启用旧版重协商
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    session = requests.Session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session

# 请求 URL
url = "https://api.jobonline.cn/jobtbao-es-api/elastic/api/position/common/v1/showlist?bodytarget=SEARCH_RESULT_PAGE"

# 完整请求头
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "E-CONTENT-PATH": "041fa762970bd0b28807e5743ee0ac1c00e07a0354e93dd741fc10e416160f8105e9c01d44628f51215e10ad3be19c9cf42973926a715423ccfd9a463164749f0861f36c4a3c3bcb4893abf4b517401e33717c253be0c9e1509112b4ebd779b6c7cff5cc67b3d4db881daab7befb2c161f17136316e32782de562657c2271bb8f966e08d67de8c2a7c62c4d5db9f736d935b6c1f1efad2dee511b18beb36924d233a06595f42cdd01fa39c9fb792863bf290c27697c0b8e0b2d17ada563d9e1d9e49917b5d511aac49055b45f6b8eb1d308a498a23b5e559bd8051adf8808f76c018f238",
    "E-SIGN": "82b2a572e8d9863fb94633cd3f96f88696617c5ae94cc9d1df962c1beaffb398",
    "E-VERSION": "v2.0.0",
    "EncryptFlag": "2",
    "Origin": "https://www.jobonline.cn",
    "Referer": "https://www.jobonline.cn/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
    "msha": "1",
    "platform": "3",
    "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Microsoft Edge";v="146"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}

# 请求体
data = '''{"businessData":"b1bde1a17058c4315d33d4567a1843f3552c5bf81f71414c65b17a83a0a1859ae941199a53eba5092744b55fcae8e0803459c34641902fd759c7acaf17fa68e3f3491f178404e088a5173c407213a775e97e680f32f9017a60c3d4178a788f662ec753f8d78f4235acfabae7cfeb4bca1b2a3abca62c240bb5eb39716b4d3b1e0a5c24666eb4b570b0b5e3a3a3503ceca1bf10101e1e3ac2951895ded0632e2984e6a2800dc521677f8982b84c27052999996396b50be0b8e47bf0e2f117b421841b5d1bd1e4231a392fc15d87bb954b64fe5d92976d2173bfe61a15a0233c151a44d6f5b0fcb56bb9ddc969e33d2470243ded6e70bf9e4c29c7e3699357f4e07d069e91b6cb17852150771a7921726bc6d599b5653c9c4170fcb695c6d571644c9d81282751ba93fbea789207de63f502dcfaf29cc3a5caef62d66cf62a1379bbb5cab7e1992abda6dce81efbb3ea41488131e885fec7bc3351d0565daba9a3f56e02b07eb73619aa883aab933592ad88b3bd9fb5e9f2fdc2e965f18e21e4269b2a6af887778cafd7eddb83da7b10c233584a7cfdd890ca85f7ab97ac76cde3d8024805fe42ab07514f6059350bd236211b117346cd7ffefc27f5142ddd78317df4645bda6f365e98805de713b80de6ce1844fb910d787573db874d8001321906df61614b668ea6fa7e479919b32e04ec225f92e512f3639023f39385faddf75bc93aefdcbe3510adce9fa1ba89619b390f2bb0128c5eab433a5c973b7eb479c08d9812c77f50ef0e0acd5b719f035e3c1667021d2e7dc30527485ab0ef17a1de4aef2f02046a9e2da99c8cf9f098cd"}'''
# 如何得到businessData的加密过程?

# 使用修复后的 session 发送请求（关键修复）
session = get_legacy_session()
response = session.post(url, headers=headers, data=data.encode('utf-8'))

# 输出结果
print("状态码:", response.status_code)
print("响应内容:", response.text)