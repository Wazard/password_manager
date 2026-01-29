import customtkinter as ctk
import json
import secrets
import string
from tkinter import messagebox

# Existing backend imports
from core import encryption
from core import storage_handler
from core import storage_compression
from core import data_handler
from core import password_generator

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_SUCCESS = "#2ECC71"  # Green
COLOR_DANGER = "#E74C3C"   # Red
COLOR_BG_CARD = "#2B2B2B"

class PasswordManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Secure Vault")
        self.geometry("480x360") # Adjusted height for better proportions
        
        self.master_password = ""
        self.vault_data = {}
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.show_auth_screen()

    def clear_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def save_vault(self):
        try:
            json_data = json.dumps(self.vault_data)
            compressed = storage_compression.compress_data(json_data)
            encrypted = encryption.encrypt_data(compressed, self.master_password)
            storage_handler.write_vault(encrypted)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {e}")
            return False

    # --- Screen 1: Authentication ---
    def show_auth_screen(self):
        self.clear_screen()
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.place(relx=0.5, rely=0.4, anchor="center")
        
        ctk.CTkLabel(frame, text="Password Manager", font=("Arial", 28, "bold")).pack(pady=20)
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="insert pass.master", show="*", width=250)
        self.pass_entry.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(frame, text="")
        self.status_label.pack()
        
        ctk.CTkButton(frame, text="Login", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        pwd = self.pass_entry.get()
        raw_blob = storage_handler.read_vault()
        if not raw_blob:
            self.master_password = pwd
            self.vault_data = {}
            self.show_dashboard()
            return
        try:
            decrypted = encryption.decrypt_data(raw_blob, pwd)
            decompressed = storage_compression.decompress_data(decrypted)
            self.vault_data = json.loads(decompressed)
            self.master_password = pwd
            self.status_label.configure(text="correct", text_color=COLOR_SUCCESS)
            self.after(500, self.show_dashboard)
        except Exception:
            self.status_label.configure(text="wrong", text_color=COLOR_DANGER)

    # --- Screen 2 & 3: Dashboard (Enhanced) ---
    def show_dashboard(self):
        self.clear_screen()
        
        # Header - Centered Title
        header = ctk.CTkFrame(self.container, height=60, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text="Accounts", font=("Arial", 22, "bold")).pack(expand=True)
        
        scroll = ctk.CTkScrollableFrame(self.container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        if not self.vault_data:
            ctk.CTkLabel(scroll, text="no accounts", font=("Arial", 16)).pack(pady=100)
            ctk.CTkButton(scroll, text="ADD ACCOUNT", fg_color=COLOR_SUCCESS, 
                          command=self.show_add_screen).pack()
        else:
            # Grid layout - Balanced/Justified Tiles
            scroll.grid_columnconfigure((0, 1), weight=1)
            for i, service in enumerate(self.vault_data.keys()):
                btn = ctk.CTkButton(scroll, text=service, height=80,
                                   fg_color=COLOR_BG_CARD,
                                   command=lambda s=service: self.show_details(s))
                btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")

        # Global Actions Footer - Justified Buttons
        footer = ctk.CTkFrame(self.container, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=20, padx=20)
        
        ctk.CTkButton(footer, text="Add Account", command=self.show_add_screen).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(footer, text="List All", command=self.show_list_all).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(footer, text="Gen Pass", command=self.show_gen_pass_screen).pack(side="left", expand=True, padx=5)

    # --- Screen 4: Add/Modify ---
    def show_add_screen(self, edit_service=None):
        self.clear_screen()
        title = "NEW ACCOUNT" if not edit_service else f"MODIFY {edit_service}"
        
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text=title, font=("Arial", 22, "bold")).pack(pady=10)
        
        form = ctk.CTkFrame(self.container, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(form, text="Account").pack(anchor="w")
        acc_entry = ctk.CTkEntry(form)
        acc_entry.pack(fill="x", pady=(0, 15))
        if edit_service: acc_entry.insert(0, edit_service); acc_entry.configure(state="disabled")

        ctk.CTkLabel(form, text="Username").pack(anchor="w")
        user_entry = ctk.CTkEntry(form)
        user_entry.pack(fill="x", pady=(0, 15))
        if edit_service: user_entry.insert(0, self.vault_data[edit_service]['user'])

        ctk.CTkLabel(form, text="Password").pack(anchor="w")
        pwd_frame = ctk.CTkFrame(form, fg_color="transparent")
        pwd_frame.pack(fill="x")
        pwd_entry = ctk.CTkEntry(pwd_frame)
        pwd_entry.pack(side="left", fill="x", expand=True)
        if edit_service: pwd_entry.insert(0, self.vault_data[edit_service]['pass'])
        
        ctk.CTkButton(pwd_frame, text="GENERATE", width=80, 
                      command=lambda: [pwd_entry.delete(0, 'end'), pwd_entry.insert(0, password_generator.generate_secure_password())]).pack(side="right", padx=(5, 0))

        def save_action():
            service = acc_entry.get()
            if not service: return
            self.vault_data[service] = {"user": user_entry.get(), "pass": pwd_entry.get()}
            if self.save_vault(): self.show_dashboard()

        ctk.CTkButton(self.container, text="SAVE", fg_color=COLOR_SUCCESS, command=save_action).pack(pady=30)

    # --- Screen 5: Account Detail (Selectable Fields) ---
    def show_details(self, service):
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text=service, font=("Arial", 22, "bold")).pack(pady=20)
        
        detail_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        detail_frame.pack(padx=40, fill="x")
        
        # User UI (Unaltered placement)
        ctk.CTkLabel(detail_frame, text="Username:", font=("Arial", 12, "bold")).pack(anchor="w")
        user_disp = ctk.CTkEntry(detail_frame, fg_color="transparent", border_width=0)
        user_disp.insert(0, self.vault_data[service]['user'])
        user_disp.configure(state="readonly") # Makes it selectable/copyable but not editable
        user_disp.pack(anchor="w", fill="x", pady=(0, 20))
        
        # Password UI (Unaltered placement)
        ctk.CTkLabel(detail_frame, text="Password:", font=("Arial", 12, "bold")).pack(anchor="w")
        pass_disp = ctk.CTkEntry(detail_frame, fg_color="transparent", border_width=0)
        pass_disp.insert(0, self.vault_data[service]['pass'])
        pass_disp.configure(state="readonly")
        pass_disp.pack(anchor="w", fill="x")

        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=40)
        
        ctk.CTkButton(btn_frame, text="MODIFY", fg_color=COLOR_SUCCESS, 
                      command=lambda: self.show_add_screen(service)).pack(side="left", padx=10)
        
        def delete_action():
            if messagebox.askyesno("Confirm", f"Delete {service}?"):
                if data_handler.delete_entry(self.vault_data, service):
                    self.save_vault()
                    self.show_dashboard()

        ctk.CTkButton(btn_frame, text="DELETE", fg_color=COLOR_DANGER, command=delete_action).pack(side="left", padx=10)

    # --- Screen 6: All Accounts List ---
    def show_list_all(self):
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text="all accounts", font=("Arial", 22, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(self.container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        for service in self.vault_data.keys():
            ctk.CTkButton(scroll, text=service, anchor="w", fg_color=COLOR_BG_CARD,
                         command=lambda s=service: self.show_details(s)).pack(fill="x", pady=5)

    # --- Screen 7: Animated Password Generator (New) ---
    def show_gen_pass_screen(self):
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.place(relx=0.5, rely=0.4, anchor="center")
        
        ctk.CTkLabel(frame, text="Secure Generator", font=("Arial", 22, "bold")).pack(pady=20)
        
        self.gen_display = ctk.CTkEntry(frame, font=("Courier", 24), width=320, justify="center")
        self.gen_display.pack(pady=20)
        
        final_password = password_generator.generate_secure_password() # e.g. "a1b2-c3d4-e5f6"
        self.animate_password(final_password, 0)

    def animate_password(self, target, step):
        # target length is 14. 12 hex chars + 2 dashes.
        # indices of hex chars: [0,1,2,3, 5,6,7,8, 10,11,12,13]
        hex_indices = [i for i, char in enumerate(target) if char != '-']
        total_steps = len(hex_indices)
        duration = 0.8 # seconds
        interval = int((duration / total_steps) * 1000)

        if step <= total_steps:
            current_view = list(target)
            # Fill locked characters up to 'step'
            for i in range(step):
                idx = hex_indices[i]
                current_view[idx] = target[idx]
            
            # Fill remaining with random noise
            for i in range(step, total_steps):
                idx = hex_indices[i]
                current_view[idx] = secrets.choice("0123456789abcdef")
            
            self.gen_display.delete(0, 'end')
            self.gen_display.insert(0, "".join(current_view))
            
            if step < total_steps:
                self.after(interval, lambda: self.animate_password(target, step + 1))
            else:
                self.gen_display.configure(state="readonly") # Make copyable after completion

if __name__ == "__main__":
    app = PasswordManagerGUI()
    app.mainloop()