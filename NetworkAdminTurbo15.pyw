import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import customtkinter as ctk
import os
import platform
import subprocess
import threading
import re
import time
import datetime
import configparser
import shutil
import socket
from concurrent.futures import ThreadPoolExecutor

# --- CONFIGURATION VISUELLE ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class SuperPingMonitor(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Network Admin Turbo V1.5 - By Popov © 2026")
        self.geometry("1100x550") 
        
        # Chemins pour la persistance des données
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.base_path, "config.ini")
        self.default_list = os.path.join(self.base_path, "liste_auto.txt")
        self.backup_dir = os.path.join(self.base_path, "backups")
        
        # Création du dossier de secours pour les listes
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        self.widgets_items = {} # Stockage des cadres IP pour les couleurs
        self.machines_liste = {}
        self.scan_results_cache = {} # Cache pour stocker les états online/offline
        self.is_scanning = False
        
        # Etats pour les tris cycliques
        self.tri_mode = 0 # 0: IP, 1: NOM, 2: MAC
        self.tri_status = 0 # 0: Normal, 1: Online First, 2: Offline First

        # Gestionnaire pour le scan automatique après action (ajout ou tri)
        self.timer_action = None

        self.setup_ui()
        self.charger_configuration()

    def setup_ui(self):
        """Définit la structure de la fenêtre"""
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # BARRE SUPÉRIEURE : Fichier, Préfixe IP et Plage (Start/End)
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.top_frame, text="Fichier :").grid(row=0, column=0, padx=5)
        self.entry_file = ctk.CTkEntry(self.top_frame, width=250)
        self.entry_file.grid(row=0, column=1, padx=5)
        ctk.CTkButton(self.top_frame, text="Parcourir", width=80, command=self.choisir_fichier).grid(row=0, column=2, padx=5)

        ctk.CTkLabel(self.top_frame, text="IP :").grid(row=0, column=3, padx=5)
        self.entry_prefix = ctk.CTkEntry(self.top_frame, width=100)
        self.entry_prefix.grid(row=0, column=4, padx=5)

        ctk.CTkLabel(self.top_frame, text="Plage :").grid(row=0, column=5, padx=5)
        self.entry_start = ctk.CTkEntry(self.top_frame, width=40)
        self.entry_start.grid(row=0, column=6, padx=2)
        self.entry_end = ctk.CTkEntry(self.top_frame, width=40)
        self.entry_end.grid(row=0, column=7, padx=2)

        # BOUTONS DE TRI CYCLIQUES
        self.btn_tri_mode = ctk.CTkButton(self.top_frame, text="TRI: IP", width=80, fg_color="#5d6d7e", command=self.cycle_tri_mode)
        self.btn_tri_mode.grid(row=0, column=8, padx=10)
        
        self.btn_tri_status = ctk.CTkButton(self.top_frame, text="STATUT: MELANGE", width=110, fg_color="#5d6d7e", command=self.cycle_tri_status)
        self.btn_tri_status.grid(row=0, column=9, padx=5)

        # GAUCHE : Appareils enregistrés
        self.frame_scroll = ctk.CTkScrollableFrame(self, label_text="Parc Réseau Enregistré")
        self.frame_scroll.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.container_connus = ctk.CTkFrame(self.frame_scroll, fg_color="transparent")
        self.container_connus.pack(fill="both", expand=True)
        self.container_connus.grid_columnconfigure((0, 1, 2), weight=1)

        # DROITE : Nouveaux appareils non répertoriés
        self.frame_inconnus = ctk.CTkScrollableFrame(self, label_text="Nouveaux Appareils détectés", fg_color="#1a1a1a")
        self.frame_inconnus.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.container_inconnus = ctk.CTkFrame(self.frame_inconnus, fg_color="transparent")
        self.container_inconnus.pack(fill="both", expand=True)

        # LOGS : Historique des actions
        self.txt_log = ctk.CTkTextbox(self, height=100, fg_color="black", text_color="#00ff00", font=("Consolas", 11))
        self.txt_log.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # CONTRÔLES : Lancement et Scan Auto
        self.ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_frame.grid(row=3, column=0, columnspan=2, pady=10)

        self.btn_scan = ctk.CTkButton(self.ctrl_frame, text="LANCER SCAN TURBO", command=self.start_manual_scan, 
                                      width=250, height=40, font=("Arial", 13, "bold"), fg_color="#1f538d")
        self.btn_scan.pack(side="left", padx=20)

        self.check_auto = ctk.CTkCheckBox(self.ctrl_frame, text="Scan Auto (min) :", command=self.toggle_auto_scan)
        self.check_auto.pack(side="left", padx=5)

        self.entry_delay = ctk.CTkEntry(self.ctrl_frame, width=50)
        self.entry_delay.pack(side="left", padx=5)
        
        self.progress_bar = ctk.CTkProgressBar(self, height=10)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    def declencher_scan_differe(self, ms):
        """Annule le timer précédent et lance un nouveau compte à rebours pour le scan"""
        if self.timer_action:
            self.after_cancel(self.timer_action)
        self.timer_action = self.after(ms, self.start_manual_scan)

    def cycle_tri_mode(self):
        """Change le mode de tri et déclenche un scan auto après 2s"""
        self.tri_mode = (self.tri_mode + 1) % 3
        modes = ["TRI: IP", "TRI: NOM", "TRI: MAC"]
        self.btn_tri_mode.configure(text=modes[self.tri_mode])
        self.refresh_interface()
        self.declencher_scan_differe(2000)

    def cycle_tri_status(self):
        """Change le tri par statut (en premier) et déclenche un scan auto après 2s"""
        self.tri_status = (self.tri_status + 1) % 3
        stats = ["STATUT: TOUS", "STATUT: ONLINE 1er", "STATUT: OFFLINE 1er"]
        self.btn_tri_status.configure(text=stats[self.tri_status])
        self.refresh_interface()
        self.declencher_scan_differe(2000)

    def log(self, message):
        """Affiche un message avec l'heure dans la console"""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert("end", f"[{ts}] {message}\n")
        self.txt_log.see("end")

    def charger_configuration(self):
        """Charge les paramètres depuis config.ini ou met les valeurs par défaut"""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file, encoding='utf-8')
                s = config['SETTINGS']
                f_path = s.get('fichier', self.default_list)
                if not os.path.exists(f_path): f_path = self.default_list
                self.entry_file.insert(0, f_path)
                self.entry_prefix.insert(0, s.get('prefix', '192.168.1.'))
                self.entry_start.insert(0, s.get('start', '1'))
                self.entry_end.insert(0, s.get('end', '254'))
                self.entry_delay.insert(0, s.get('delay', '5'))
            except: pass
        else:
            self.entry_file.insert(0, self.default_list)
            self.entry_prefix.insert(0, "192.168.1.")
            self.entry_start.insert(0, "1")
            self.entry_end.insert(0, "254")
            self.entry_delay.insert(0, "5")
        self.refresh_interface()

    def sauver_configuration(self):
        """Enregistre les entrées actuelles dans le fichier config.ini"""
        try:
            config = configparser.ConfigParser()
            config['SETTINGS'] = {
                'fichier': self.entry_file.get(), 
                'prefix': self.entry_prefix.get(),
                'start': self.entry_start.get(), 
                'end': self.entry_end.get(), 
                'delay': self.entry_delay.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
        except: pass

    def archiver_liste(self):
        """Crée une copie de sécurité de la liste avant modification"""
        f_source = self.entry_file.get().strip() or self.default_list
        if os.path.exists(f_source):
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            try: 
                shutil.copy2(f_source, os.path.join(self.backup_dir, f"backup_{ts}.txt"))
            except: pass

    def choisir_fichier(self):
        """Ouvre l'explorateur pour changer de fichier de parc"""
        path = filedialog.askopenfilename(title="Choisir la liste", filetypes=[("Texte", "*.txt")])
        if path:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, path)
            self.refresh_interface()
            self.sauver_configuration()

    def refresh_interface(self):
        """Reconstruit la grille visuelle COMPLÈTE des appareils enregistrés"""
        for widget in self.container_connus.winfo_children(): widget.destroy()
        path = self.entry_file.get().strip() or self.default_list
        temp_liste = []
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        parts = [p.strip() for p in line.split(",") if p.strip()]
                        if len(parts) >= 3:
                            # On utilise le cache de scan global pour le statut
                            is_online = self.scan_results_cache.get(parts[1], False)
                            temp_liste.append({'mac': parts[0].upper(), 'ip': parts[1], 'nom': parts[2], 'online': is_online})
            except: pass
        
        # Tri par MODE
        if self.tri_mode == 0: # IP
            temp_liste.sort(key=lambda x: [int(d) for d in x['ip'].split('.') if d.isdigit()])
        elif self.tri_mode == 1: # NOM
            temp_liste.sort(key=lambda x: x['nom'].lower())
        else: # MAC
            temp_liste.sort(key=lambda x: x['mac'])

        # Tri par STATUT (sans masquer les éléments)
        if self.tri_status == 1: # Online en premier
            temp_liste.sort(key=lambda x: x['online'], reverse=True)
        elif self.tri_status == 2: # Offline en premier
            temp_liste.sort(key=lambda x: x['online'])

        self.widgets_items = {}
        for i, info in enumerate(temp_liste):
            ip = info['ip']
            f = ctk.CTkFrame(self.container_connus, fg_color="#333333", border_width=1, border_color="#555")
            f.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="ew")
            
            # Application de la couleur finale
            f.configure(fg_color="#2ecc71" if info['online'] else "#e74c3c")
            
            btn_del = ctk.CTkButton(f, text="X", width=20, height=20, fg_color="#c0392b", hover_color="#e74c3c", 
                                  command=lambda t_ip=ip: self.supprimer_appareil(t_ip))
            btn_del.pack(anchor="ne", padx=2, pady=2)
            
            lbl_nom = ctk.CTkLabel(f, text=info['nom'], font=("Arial", 11, "bold"), cursor="hand2")
            lbl_nom.pack(pady=(0, 2))
            lbl_nom.bind("<Button-1>", lambda e, t_ip=ip, old_n=info['nom']: self.editer_nom(t_ip, old_n))
            
            ctk.CTkLabel(f, text=f"{ip}\n{info['mac']}", font=("Arial", 9)).pack(pady=2)
            self.widgets_items[ip] = f

    def editer_nom(self, ip, ancien_nom):
        """Permet de renommer un appareil au clic sur son nom"""
        nouveau_nom = simpledialog.askstring("Édition", f"Nouveau nom pour {ip} :", initialvalue=ancien_nom)
        if nouveau_nom and nouveau_nom.strip():
            path = self.entry_file.get().strip() or self.default_list
            try:
                lines = []
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        p = line.strip().split(",")
                        if len(p) >= 2 and p[1] == ip:
                            lines.append(f"{p[0]},{p[1]},{nouveau_nom.strip()}\n")
                        else: lines.append(line)
                with open(path, "w", encoding="utf-8") as f: f.writelines(lines)
                self.refresh_interface()
            except: pass

    def supprimer_appareil(self, ip):
        """Retire un appareil de la liste enregistrée"""
        path = self.entry_file.get().strip() or self.default_list
        if messagebox.askyesno("Confirmation", f"Supprimer {ip} du parc ?"):
            try:
                lines = []
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        p = line.strip().split(",")
                        if len(p) >= 2 and p[1] == ip: continue
                        lines.append(line)
                with open(path, "w", encoding="utf-8") as f: f.writelines(lines)
                self.refresh_interface()
            except: pass

    def ajouter_unitairement(self, mac, ip, nom, widget_frame):
        """Ajoute un appareil et déclenche un scan auto après 3s de calme"""
        current_file = self.entry_file.get().strip() or self.default_list
        try:
            with open(current_file, "a", encoding="utf-8") as f:
                f.write(f"{mac},{ip},{nom}\n")
            widget_frame.destroy()
            self.refresh_interface()
            self.log(f"Ajouté : {nom} ({ip})")
            
            self.declencher_scan_differe(3000)
            
        except: pass

    def ping_worker(self, ip):
        """Tâche de fond : Ping + ARP + Hostname"""
        f = 0x08000000 if platform.system().lower() == 'windows' else 0
        cmd = ['ping', '-n', '1', '-w', '400', ip]
        ok = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=f) == 0
        
        mac, name = "INCONNUE", f"PC_{ip.split('.')[-1]}"
        if ok:
            try:
                name = socket.gethostbyaddr(ip)[0].split('.')[0].upper()
            except: pass
            try:
                out = subprocess.check_output(["arp", "-a", ip], creationflags=f, timeout=0.5).decode('cp1252')
                m = re.search(r"([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})", out)
                if m: mac = m.group(0).upper().replace("-", ":")
            except: pass
            return (ip, True, mac, name)
        return (ip, False, None, None)

    def run_scan(self):
        """Boucle principale du scan multi-thread"""
        if self.is_scanning: return
        self.is_scanning = True
        self.btn_scan.configure(state="disabled", text="SCAN EN COURS...")
        self.archiver_liste()
        
        try:
            prefix = self.entry_prefix.get().strip()
            if not prefix.endswith('.'): prefix += '.'
            start, end = int(self.entry_start.get()), int(self.entry_end.get())
            self.sauver_configuration()

            ips = [f"{prefix}{i}" for i in range(start, end + 1)]
            self.log(f"Scan de {len(ips)} adresses...")
            
            with ThreadPoolExecutor(max_workers=100) as ex:
                results = list(ex.map(self.ping_worker, ips))

            # ON NE MET PLUS À JOUR LES WIDGETS ICI
            # On stocke tout dans le cache de scan d'abord
            nouvelle_detection_inconnue = []
            for ip, ok, mac, name in results:
                self.scan_results_cache[ip] = ok # On mémorise l'état
                
                # Si c'est un nouvel appareil (pas dans la liste enregistrée), on le garde pour plus tard
                if ok and ip not in self.widgets_items:
                    nouvelle_detection_inconnue.append((ip, name, mac))
            
            # UNE FOIS LE SCAN FINI : On remplace toute la fenêtre principale
            self.after(0, self.finaliser_affichage_scan, nouvelle_detection_inconnue)
                
        except Exception as e: 
            self.log(f"Erreur: {e}")
        finally:
            self.is_scanning = False
            self.btn_scan.configure(state="normal", text="LANCER SCAN TURBO")
            if self.check_auto.get(): self.attendre_prochain_scan()

    def finaliser_affichage_scan(self, inconnus):
        """Mise à jour finale et atomique de l'interface"""
        # 1. On reconstruit tout le parc enregistré d'un coup
        self.refresh_interface()
        
        # 2. On ajoute les nouveaux à droite
        for ip, name, mac in inconnus:
            row = ctk.CTkFrame(self.container_inconnus, fg_color="#2b2b2b")
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=f"{ip}\n({name})", font=("Arial", 9, "bold")).pack(side="left", padx=5)
            btn = ctk.CTkButton(row, text="+", width=30, height=20, fg_color="#27ae60", 
                               command=lambda m=mac, i=ip, n=name, r=row: self.ajouter_unitairement(m, i, n, r))
            btn.pack(side="right", padx=5)
            
        self.log("Scan terminé. Interface mise à jour.")

    def start_manual_scan(self):
        """Déclenche le scan manuel dans un thread séparé"""
        for w in self.container_inconnus.winfo_children(): w.destroy()
        threading.Thread(target=self.run_scan, daemon=True).start()

    def toggle_auto_scan(self):
        """Lance ou arrête le mode automatique"""
        if self.check_auto.get(): self.start_manual_scan()

    def attendre_prochain_scan(self):
        """Gère le délai avant le prochain scan auto"""
        try: sec = int(float(self.entry_delay.get()) * 60)
        except: sec = 300
        def countdown():
            for i in range(sec):
                if not self.check_auto.get(): return
                time.sleep(1)
                self.progress_bar.set((i + 1) / sec)
            if self.check_auto.get(): self.start_manual_scan()
        threading.Thread(target=countdown, daemon=True).start()

if __name__ == "__main__":
    app = SuperPingMonitor()
    app.mainloop()