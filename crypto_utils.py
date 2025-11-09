
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken

# パスワードベースのキー導出関数 (PBKDF2) のための定数
SALT_SIZE = 16  # 16バイトのソルト
ITERATIONS = 480000  # 反復回数 (セキュリティ強度を決定する重要な要素)
KEY_LENGTH = 32  # 32バイト (256ビット) のキー長

def derive_key(password: str, salt: bytes) -> bytes:
    """パスワードとソルトから暗号化キーを導出する"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    # FernetはURLセーフなbase64エンコードされたキーを要求する
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def encrypt_file(file_path: str, password: str) -> bool:
    """ファイルを暗号化して .smai 形式で保存する"""
    try:
        # 1. ファイルコンテンツを読み込む
        with open(file_path, 'rb') as f:
            data = f.read()

        # 2. 新しいソルトを生成
        salt = os.urandom(SALT_SIZE)

        # 3. パスワードとソルトからキーを導出
        key = derive_key(password, salt)

        # 4. データを暗号化
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)

        # 5. ソルトと暗号化データを新しいファイルに書き込む
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
        # 1. 暗号化ファイルを読み込む
        with open(file_path, 'rb') as f:
            # 最初の16バイトがソルト
            salt = f.read(SALT_SIZE)
            # 残りが暗号化データ
            encrypted_data = f.read()

        # 2. パスワードとソルトからキーを導出
        key = derive_key(password, salt)

        # 3. データを復号
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)

        # 4. 復号したデータを新しいファイルに書き込む
        output_path = os.path.splitext(file_path)[0]
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
            
        return True
    except InvalidToken:
        # パスワードが違う、またはファイルが破損している場合
        print("復号に失敗しました: パスワードが違うか、ファイルが破損しています。")
        return False
    except Exception as e:
        print(f"復号エラー: {e}")
        return False
