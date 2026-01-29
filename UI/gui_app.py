import customtkinter as ctk
import json
import secrets
from tkinter import messagebox

# Existing backend imports
from core import encryption
from core import storage_handler
from core import storage_compression
from core import data_handler
from core import password_generator
from localization.language_manager import LanguageManager

# --- Main Application ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_SUCCESS = "#2ECC71"
COLOR_DANGER = "#E74C3C"
COLOR_BG_CARD = "#2B2B2B"

ANIMATION_DURATION = 1.2 # seconds

class PasswordManagerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Localization State
        self.lang_manager = LanguageManager()
        self.current_lang = "en"
        self.current_view = "auth"
        self.active_service = None # For detail/modify tracking
        
        self.title("Secure Vault")
        self.geometry("480x360")
        
        self.master_password = ""
        self.vault_data = {}
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        
        self.show_auth_screen()

    def t(self, key, **kwargs):
        """Translation helper function."""
        return self.lang_manager.get_text(key, self.current_lang, **kwargs)

    def change_language(self, new_lang):
        """Refresh the current screen with the new language."""
        self.current_lang = new_lang
        # Real-time UI refresh based on state
        view_map = {
            "auth": self.show_auth_screen,
            "dashboard": self.show_dashboard,
            "add": lambda: self.show_add_screen(),
            "modify": lambda: self.show_add_screen(self.active_service),
            "details": lambda: self.show_details(self.active_service),
            "list_all": self.show_list_all,
            "generator": self.show_gen_pass_screen
        }
        view_map[self.current_view]()

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
        self.current_view = "auth"
        self.clear_screen()
        
        # Language Selector Top Right
        lang_menu = ctk.CTkOptionMenu(self.container, values=["en"], 
                                      command=self.change_language, width=60)
        lang_menu.set(self.current_lang)
        lang_menu.place(relx=0.98, rely=0.02, anchor="ne")

        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.place(relx=0.5, rely=0.4, anchor="center")
        
        ctk.CTkLabel(frame, text=self.t("auth.title"), font=("Arial", 28, "bold")).pack(pady=20)
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text=self.t("auth.placeholder"), show="*", width=250)
        self.pass_entry.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(frame, text="")
        self.status_label.pack()
        ctk.CTkButton(frame, text=self.t("auth.login_btn"), command=self.attempt_login).pack(pady=20)

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
            self.status_label.configure(text=self.t("auth.correct"), text_color=COLOR_SUCCESS)
            self.after(500, self.show_dashboard)
        except Exception:
            self.status_label.configure(text=self.t("auth.wrong"), text_color=COLOR_DANGER)

    # --- Screen 2 & 3: Dashboard ---
    def show_dashboard(self):
        self.current_view = "dashboard"
        self.clear_screen()
        
        header = ctk.CTkFrame(self.container, height=60, fg_color="transparent")
        header.pack(fill="x", pady=10)
        ctk.CTkLabel(header, text=self.t("dashboard.title"), font=("Arial", 22, "bold")).pack(expand=True)
        
        scroll = ctk.CTkScrollableFrame(self.container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        if not self.vault_data:
            ctk.CTkLabel(scroll, text=self.t("dashboard.no_accounts"), font=("Arial", 16)).pack(pady=100)
            ctk.CTkButton(scroll, text=self.t("dashboard.add_btn").upper(), fg_color=COLOR_SUCCESS, 
                          command=self.show_add_screen).pack()
        else:
            scroll.grid_columnconfigure((0, 1), weight=1)
            for i, service in enumerate(self.vault_data.keys()):
                btn = ctk.CTkButton(scroll, text=service, height=80,
                                   fg_color=COLOR_BG_CARD,
                                   command=lambda s=service: self.show_details(s))
                btn.grid(row=i//2, column=i%2, padx=10, pady=10, sticky="ew")

        footer = ctk.CTkFrame(self.container, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=20, padx=20)
        ctk.CTkButton(footer, text=self.t("dashboard.add_btn"), command=self.show_add_screen).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(footer, text=self.t("dashboard.list_all"), command=self.show_list_all).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(footer, text=self.t("dashboard.gen_pass"), command=self.show_gen_pass_screen).pack(side="left", expand=True, padx=5)

    # --- Screen 4: Add/Modify ---
    def show_add_screen(self, edit_service=None):
        self.active_service = edit_service
        self.current_view = "modify" if edit_service else "add"
        self.clear_screen()
        title = self.t("forms.new_title") if not edit_service else self.t("forms.modify_title", service=edit_service)
        
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text=title, font=("Arial", 22, "bold")).pack(pady=10)
        
        form = ctk.CTkFrame(self.container, fg_color="transparent")
        form.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(form, text=self.t("forms.account")).pack(anchor="w")
        acc_entry = ctk.CTkEntry(form)
        acc_entry.pack(fill="x", pady=(0, 15))
        if edit_service: acc_entry.insert(0, edit_service); acc_entry.configure(state="disabled")

        ctk.CTkLabel(form, text=self.t("forms.username")).pack(anchor="w")
        user_entry = ctk.CTkEntry(form)
        user_entry.pack(fill="x", pady=(0, 15))
        if edit_service: user_entry.insert(0, self.vault_data[edit_service]['user'])

        ctk.CTkLabel(form, text=self.t("forms.password")).pack(anchor="w")
        pwd_frame = ctk.CTkFrame(form, fg_color="transparent")
        pwd_frame.pack(fill="x")
        pwd_entry = ctk.CTkEntry(pwd_frame)
        pwd_entry.pack(side="left", fill="x", expand=True)
        if edit_service: pwd_entry.insert(0, self.vault_data[edit_service]['pass'])
        
        ctk.CTkButton(pwd_frame, text=self.t("forms.generate"), width=80, 
                      command=lambda: [pwd_entry.delete(0, 'end'), pwd_entry.insert(0, password_generator.generate_secure_password())]).pack(side="right", padx=(5, 0))

        def save_action():
            service = acc_entry.get()
            if not service: return
            self.vault_data[service] = {"user": user_entry.get(), "pass": pwd_entry.get()}
            if self.save_vault(): self.show_dashboard()

        ctk.CTkButton(self.container, text=self.t("forms.save"), fg_color=COLOR_SUCCESS, command=save_action).pack(pady=30)

    # --- Screen 5: Account Detail ---
    def show_details(self, service):
        self.active_service = service
        self.current_view = "details"
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text=service, font=("Arial", 22, "bold")).pack(pady=20)
        
        detail_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        detail_frame.pack(padx=40, fill="x")
        
        ctk.CTkLabel(detail_frame, text=self.t("details.username_label"), font=("Arial", 12, "bold")).pack(anchor="w")
        user_disp = ctk.CTkEntry(detail_frame, fg_color="transparent", border_width=0)
        user_disp.insert(0, self.vault_data[service]['user'])
        user_disp.configure(state="readonly")
        user_disp.pack(anchor="w", fill="x", pady=(0, 20))
        
        ctk.CTkLabel(detail_frame, text=self.t("details.password_label"), font=("Arial", 12, "bold")).pack(anchor="w")
        pass_disp = ctk.CTkEntry(detail_frame, fg_color="transparent", border_width=0)
        pass_disp.insert(0, self.vault_data[service]['pass'])
        pass_disp.configure(state="readonly")
        pass_disp.pack(anchor="w", fill="x")

        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=40)
        ctk.CTkButton(btn_frame, text=self.t("details.modify"), fg_color=COLOR_SUCCESS, 
                      command=lambda: self.show_add_screen(service)).pack(side="left", padx=10)
        
        def delete_action():
            if messagebox.askyesno("Confirm", self.t("details.delete_confirm", service=service)):
                if data_handler.delete_entry(self.vault_data, service):
                    self.save_vault()
                    self.show_dashboard()
        ctk.CTkButton(btn_frame, text=self.t("details.delete"), fg_color=COLOR_DANGER, command=delete_action).pack(side="left", padx=10)

    # --- Screen 6: All Accounts List ---
    def show_list_all(self):
        self.current_view = "list_all"
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        ctk.CTkLabel(self.container, text=self.t("list_all.title"), font=("Arial", 22, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(self.container)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        for service in self.vault_data.keys():
            ctk.CTkButton(scroll, text=service, anchor="w", fg_color=COLOR_BG_CARD,
                         command=lambda s=service: self.show_details(s)).pack(fill="x", pady=5)

    # --- Screen 7: Animated Password Generator ---
    def show_gen_pass_screen(self):
        self.current_view = "generator"
        self.clear_screen()
        ctk.CTkButton(self.container, text="←", width=30, command=self.show_dashboard).pack(anchor="nw", padx=10, pady=10)
        
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        frame.place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(frame, text=self.t("generator.title"), font=("Arial", 22, "bold")).pack(pady=20)
        
        self.gen_display = ctk.CTkEntry(frame, font=("Courier", 24), width=320, justify="center")
        self.gen_display.pack(pady=20)
        
        final_password = password_generator.generate_secure_password()
        self.animate_password(final_password, 0)

    def animate_password(self, target, step):
            # Configuration - using 0.8s as the standard duration
            ANIMATION_DURATION = 0.8 
            hex_indices = [i for i, char in enumerate(target) if char != '-']
            total_hex = len(hex_indices)
            
            # Double the steps: Phase 1 (Jumble) takes total_hex steps, 
            # Phase 2 (Lock) takes total_hex steps.
            total_animation_steps = total_hex * 2 
            interval = int((ANIMATION_DURATION / total_animation_steps) * 1000)

            current_view = list(target)

            if step < total_hex:
                # PHASE 1: First half of duration - All characters animate randomly
                for idx in hex_indices:
                    current_view[idx] = secrets.choice("0123456789abcdef")
            else:
                # PHASE 2: Second half of duration - Locking begins from left to right
                lock_index = step - total_hex
                for i, idx in enumerate(hex_indices):
                    if i <= lock_index:
                        current_view[idx] = target[idx]
                    else:
                        current_view[idx] = secrets.choice("0123456789abcdef")

            # Update Display
            self.gen_display.delete(0, 'end')
            self.gen_display.insert(0, "".join(current_view))
            
            if step < total_animation_steps - 1:
                # Schedule next frame
                self.after(interval, lambda: self.animate_password(target, step + 1))
            else:
                # Finalize: ensure target is perfectly set and make selectable
                self.gen_display.delete(0, 'end')
                self.gen_display.insert(0, target)
                self.gen_display.configure(state="readonly")