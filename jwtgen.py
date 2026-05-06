from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
import my_pb2
import output_pb2
import warnings
from urllib3.exceptions import InsecureRequestWarning
from typing import Optional
import uvicorn
import json
from datetime import datetime
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
import hashlib

# Disable SSL warning
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Constants
AES_KEY = b'Yg&tc%DEuh6%Zc^8'
AES_IV = b'6oyZDr22E3ychjM%'

# Store hashed keys instead of plain text for better security
VALID_API_KEYS_HASHED = [
    hashlib.sha256("SEMY".encode()).hexdigest(),
    hashlib.sha256("SEMYPAPA".encode()).hexdigest(),
    hashlib.sha256("HELLOSEMY".encode()).hexdigest()
]

# FastAPI setup
app = FastAPI(
    title="FreeFire Token API",
    description="API for FreeFire token generation with key authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize cache
@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

def validate_api_key(api_key: str) -> bool:
    """Validate the API key by comparing its hash"""
    if not api_key:
        return False
    # Hash the provided key and compare with stored hashes
    provided_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return provided_key_hash in VALID_API_KEYS_HASHED

def get_token(password: str, uid: str) -> Optional[dict]:
    try:
        url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
        headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close"
        }
        data = {
            "uid": uid,
            "password": password,
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067"
        }
        res = requests.post(url, headers=headers, data=data, timeout=10)
        if res.status_code != 200:
            return None
        token_json = res.json()
        if "access_token" in token_json and "open_id" in token_json:
            return token_json
        else:
            return None
    except Exception:
        return None

def encrypt_message(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)

def parse_response(content: str) -> dict:
    response_dict = {}
    lines = content.split("\n")
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            response_dict[key.strip()] = value.strip().strip('"')
    return response_dict

@app.get("/")
async def root():
    return {
        "message": "FreeFire Token API",
        "status": "active",
        "version": "1.0.0",
        "owner": "@Unknown_Reason07",
        "endpoints": {
            "/token": "Get FreeFire token (requires key, uid, password)",
            "/validate-key": "Validate API key",
            "/docs": "API documentation",
            "/redoc": "Alternative documentation"
        }
    }

@app.get("/token")
@cache(expire=25200)  # 7 hours cache
async def get_single_response(
    key: str = Query(..., description="API key for authentication"),
    uid: str = Query(..., description="User ID"),
    password: str = Query(..., description="Password")
):
    """
    Get FreeFire token with key authentication.
    
    Parameters:
    - key: API key (required)
    - uid: User ID
    - password: Password
    
    Returns:
    - JSON response with token or error message
    """
    
    # Key validation
    if not validate_api_key(key):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Invalid or missing key 🔐",
                "message": "Please provide a valid API key",
                "owner": "@semy0here",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Get token data
    token_data = get_token(password, uid)
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail={
                "uid": uid,
                "status": "invalid",
                "message": "Wrong UID or Password. Please check and try again.",
                "credit": "Ghost TEAM",
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Prepare game data
    game_data = my_pb2.GameData()
    game_data.timestamp = "2024-12-05 18:15:32"
    game_data.game_name = "free fire"
    game_data.game_version = 1
    game_data.version_code = "1.108.3"
    game_data.os_info = "Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)"
    game_data.device_type = "Handheld"
    game_data.network_provider = "Verizon Wireless"
    game_data.connection_type = "WIFI"
    game_data.screen_width = 1280
    game_data.screen_height = 960
    game_data.dpi = "240"
    game_data.cpu_info = "ARMv7 VFPv3 NEON VMH | 2400 | 4"
    game_data.total_ram = 5951
    game_data.gpu_name = "Adreno (TM) 640"
    game_data.gpu_version = "OpenGL ES 3.0"
    game_data.user_id = "Google|74b585a9-0268-4ad3-8f36-ef41d2e53610"
    game_data.ip_address = "172.190.111.97"
    game_data.language = "en"
    game_data.open_id = token_data['open_id']
    game_data.access_token = token_data['access_token']
    game_data.platform_type = 4
    game_data.device_form_factor = "Handheld"
    game_data.device_model = "Asus ASUS_I005DA"
    game_data.field_60 = 32968
    game_data.field_61 = 29815
    game_data.field_62 = 2479
    game_data.field_63 = 914
    game_data.field_64 = 31213
    game_data.field_65 = 32968
    game_data.field_66 = 31213
    game_data.field_67 = 32968
    game_data.field_70 = 4
    game_data.field_73 = 2
    game_data.library_path = "/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/lib/arm"
    game_data.field_76 = 1
    game_data.apk_info = "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-QPvBnTUhYWE-7DMZSOGdmA==/base.apk"
    game_data.field_78 = 6
    game_data.field_79 = 1
    game_data.os_architecture = "32"
    game_data.build_number = "2019117877"
    game_data.field_85 = 1
    game_data.graphics_backend = "OpenGLES2"
    game_data.max_texture_units = 16383
    game_data.rendering_api = 4
    game_data.encoded_field_89 = "\u0017T\u0011\u0017\u0002\b\u000eUMQ\bEZ\u0003@ZK;Z\u0002\u000eV\ri[QVi\u0003\ro\t\u0007e"
    game_data.field_92 = 9204
    game_data.marketplace = "3rd_party"
    game_data.encryption_key = "KqsHT2B4It60T/65PGR5PXwFxQkVjGNi+IMCK3CFBCBfrNpSUA1dZnjaT3HcYchlIFFL1ZJOg0cnulKCPGD3C3h1eFQ="
    game_data.total_storage = 111107
    game_data.field_97 = 1
    game_data.field_98 = 1
    game_data.field_99 = "4"
    game_data.field_100 = "4"
    
    try:
        # Serialize and encrypt data
        serialized_data = game_data.SerializeToString()
        encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_data)
        edata = binascii.hexlify(encrypted_data).decode()

        # Make request to external API
        url = "https://loginbp.common.ggbluefox.com/MajorLogin"
        headers = {
            'User-Agent': "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)",
            'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip",
            'Content-Type': "application/octet-stream",
            'Expect': "100-continue",
            'X-Unity-Version': "2018.4.11f1",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB53"
        }

        response = requests.post(url, data=bytes.fromhex(edata), headers=headers, verify=False)

        if response.status_code == 200:
            example_msg = output_pb2.Garena_420()
            try:
                example_msg.ParseFromString(response.content)
                response_dict = parse_response(str(example_msg))
                
                return {
                    "uid": uid,
                    "status": response_dict.get("status", "N/A"),
                    "token": response_dict.get("token", "N/A"),
                    "key_used": "******",  # Fully hidden key
                    "credit": "Ghost TEAM",
                    "timestamp": datetime.now().isoformat(),
                    "cache": "Enabled (7 hours)"
                }
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "uid": uid,
                        "error": f"Failed to deserialize the response: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }
                )
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "uid": uid,
                    "error": f"Failed to get response: HTTP {response.status_code}, {response.reason}",
                    "timestamp": datetime.now().isoformat()
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "uid": uid,
                "error": f"Internal error occurred: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/validate-key")
async def validate_key_endpoint(
    key: str = Query(..., description="API key to validate")
):
    """
    Validate if an API key is valid.
    
    Parameters:
    - key: API key to validate
    
    Returns:
    - JSON response indicating if key is valid
    """
    
    is_valid = validate_api_key(key)
    
    return {
        "valid": is_valid,
        "key_provided": "******",  # Fully hidden
        "message": "Key is valid" if is_valid else "Key is invalid",
        "owner": "@semy0here",
        "timestamp": datetime.now().isoformat(),
        "hint": "Contact owner for valid API key"
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "FreeFire Token API",
        "version": "1.0.0",
        "security": "API key authentication enabled"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}
    )

# Error handler for 404
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "available_endpoints": ["/", "/token", "/validate-key", "/health", "/docs", "/redoc"]
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
