
import customtkinter as ctk
from tkinter import filedialog
import os
import threading
from crypto_utils import encrypt_file, decrypt_file
import sys
import ctypes
from tkinterdnd2 import DND_FILES, TkinterDnD

class App(TkinterDnD.Tk, ctk.CTk):
    def __init__(self):
        ctk.CTk.__init__(self)
        TkinterDnD.Tk.__init__(self)

        self.title("SHUUMAICRYPT")
        self.geometry("550x400") 

        # --- タスクバーアイコン ---
        if sys.platform == 'win32':
            myappid = 'shuumai.product.shuumaicrypt.1' # アプリケーション固有のID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.iconbitmap("icon.ico") # アプリアイコンを設定
        self.selected_file_path = ""

        ctk.set_appearance_mode("System")  
        ctk.set_default_color_theme("blue") 

        # --- メイン --- #
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- ドラッグドロップ --- #
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

        # --- ファイル選択 --- #
        self.file_label = ctk.CTkLabel(main_frame, text="ファイルが選択されていません", wraplength=480)
        self.file_label.pack(pady=(10, 5), padx=10)

        select_button = ctk.CTkButton(main_frame, text="ファイルを選択", command=self.select_file)
        select_button.pack(pady=10, padx=10)

        # --- PW入力 --- #
        password_label = ctk.CTkLabel(main_frame, text="パスワード")
        password_label.pack(pady=(20, 5), padx=10)

        self.password_entry = ctk.CTkEntry(main_frame, show="*", width=300)
        self.password_entry.pack(pady=5, padx=10)

        # --- オプション --- #
        self.delete_original_var = ctk.BooleanVar()
        delete_checkbox = ctk.CTkCheckBox(main_frame, text="処理後に元のファイルを削除する", variable=self.delete_original_var)
        delete_checkbox.pack(pady=10, padx=10)

        # --- プログレスバー --- #
        self.progressbar = ctk.CTkProgressBar(main_frame, mode='indeterminate')

        # --- アクションボタン --- #
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent") 
        button_frame.pack(pady=20, padx=10, fill="x", expand=True)

        self.encrypt_button = ctk.CTkButton(button_frame, text="暗号化", command=self.encrypt_action, width=120)
        self.encrypt_button.pack(side="left", expand=True, padx=10)

        self.decrypt_button = ctk.CTkButton(button_frame, text="復号", command=self.decrypt_action, width=120)
        self.decrypt_button.pack(side="right", expand=True, padx=10)

        # --- ステータス --- #
        self.status_label = ctk.CTkLabel(main_frame, text="準備完了", text_color="gray")
        self.status_label.pack(pady=10, padx=10, side="bottom")

    def select_file(self):
        """ファイル選択ダイアログを開き、選択されたファイルパスを保存・表示する"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.status_label.configure(text="ファイルを選択しました", text_color="gray")

    def handle_drop(self, event):
        """ドラッグ＆ドロップされたファイルを処理する"""
        file_path = event.data.strip('{}')
        
        # ファイルが存在し、単一のファイル?
        if file_path and os.path.isfile(file_path):
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.status_label.configure(text="ファイルをドロップしました", text_color="gray")


    def start_processing(self):
        """処理開始時のUI設定"""
        self.status_label.configure(text="処理中...", text_color="gray")
        self.progressbar.pack(pady=10, padx=20, fill="x")
        self.progressbar.start()
        self.encrypt_button.configure(state="disabled")
        self.decrypt_button.configure(state="disabled")
        self.update_idletasks()

    def stop_processing(self):
        """処理終了時のUI設定"""
        self.progressbar.stop()
        self.progressbar.pack_forget()
        self.encrypt_button.configure(state="normal")
        self.decrypt_button.configure(state="normal")

    def _run_encryption(self, file_path, password):
        """バックグラウンドで暗号化を実行する"""
        success = encrypt_file(file_path, password)
        self.stop_processing()
        if success:
            message = f"成功！ {os.path.basename(file_path)}.smai として保存しました"
            color = "#81C784" 
            if self.delete_original_var.get():
                try:
                    os.remove(file_path)
                    message += " (元ファイル削除済み)"
                    self.selected_file_path = ""
                    self.file_label.configure(text="ファイルが選択されていません")
                except OSError as e:
                    message = "保存成功。元ファイルの削除に失敗しました。"
                    color = "#FFB74D" 
            self.status_label.configure(text=message, text_color=color)
        else:
            self.status_label.configure(text="エラー: 暗号化に失敗しました", text_color="#E57373")

    def encrypt_action(self):
        """暗号化ボタンが押されたときのアクション"""
        if not self.selected_file_path:
            self.status_label.configure(text="エラー: 最初にファイルを選択してください", text_color="#E57373")
            return
        password = self.password_entry.get()
        if not password:
            self.status_label.configure(text="エラー: パスワードを入力してください", text_color="#E57373")
            return

        self.start_processing()
        thread = threading.Thread(target=self._run_encryption, args=(self.selected_file_path, password))
        thread.start()

    def _run_decryption(self, file_path, password):
        """バックグラウンドで復号を実行する"""
        success = decrypt_file(file_path, password)
        self.stop_processing()
        if success:
            message = f"成功！ {os.path.basename(os.path.splitext(file_path)[0])} として保存しました"
            color = "#81C784" 
            if self.delete_original_var.get():
                try:
                    os.remove(file_path)
                    message += " (元ファイル削除済み)"
                    self.selected_file_path = ""
                    self.file_label.configure(text="ファイルが選択されていません")
                except OSError as e:
                    message = "保存成功。元ファイルの削除に失敗しました。"
                    color = "#FFB74D"
            self.status_label.configure(text=message, text_color=color)
        else:
            self.status_label.configure(text="エラー: 復号に失敗しました。パスワードまたはファイルを確認してください。", text_color="#E57373")

    def decrypt_action(self):
        """復号ボタンが押されたときのアクション"""
        if not self.selected_file_path:
            self.status_label.configure(text="エラー: 最初にファイルを選択してください", text_color="#E57373")
            return
        if not self.selected_file_path.endswith(".smai"):
            self.status_label.configure(text="エラー: 復号するには .smai ファイルを選択してください", text_color="#E57373")
            return
        password = self.password_entry.get()
        if not password:
            self.status_label.configure(text="エラー: パスワードを入力してください", text_color="#E57373")
            return

        self.start_processing()
        thread = threading.Thread(target=self._run_decryption, args=(self.selected_file_path, password))
        thread.start()

if __name__ == "__main__":
    app = App()
    app.mainloop()
