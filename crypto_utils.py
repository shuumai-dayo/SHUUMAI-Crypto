
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

SALT_SIZE = 16  # 16byteソルト
ITERATIONS = 480000  # 反復回数 
KEY_LENGTH = 32  # 32byte (256ビット)のキー長

def derive_key(password: str, salt: bytes) -> bytes:
    """パスワードとソルトから暗号化キーを導出する"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_file(file_path: str, password: str) -> bool:
    """ファイルを暗号化して .smai 形式で保存"""
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        salt = os.urandom(SALT_SIZE)
        key = derive_key(password, salt)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)

        output_path = file_path + ".smai"
        with open(output_path, 'wb') as f:
            f.write(salt)
            f.write(encrypted_data)
            
        return True
    except Exception as e:
        print(f"暗号化エラー: {e}")
        return False

def decrypt_file(file_path: str, password: str) -> bool:
    """ .smai ファイルを復号する"""
    if not file_path.endswith(".smai"):
        return False

    try:
        with open(file_path, 'rb') as f:
            salt = f.read(SALT_SIZE)
            encrypted_data = f.read()

        key = derive_key(password, salt)

        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        output_path = os.path.splitext(file_path)[0]
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
            
        return True
    except InvalidToken:
        print("復号に失敗しました: パスワードが違うか、ファイルが破損しています。")
        return False
    except Exception as e:
        print(f"復号エラー: {e}")
        return False
