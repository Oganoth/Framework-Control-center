import customtkinter as ctk
import requests
import json
import logging
import subprocess
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
import time
import winreg
import psutil
import sys
import pkg_resources
import re
import os

logger = logging.getLogger(__name__)

class UpdateWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        # Configuration de la fenêtre
        self.title(self.tr("updates"))
        self.geometry("1000x500")  # Augmentation de la largeur de 700 à 1000
        self.minsize(1000, 500)    # Taille minimale correspondante
        
        # Forcer la fenêtre au premier plan
        self.attributes('-topmost', True)
        
        # Initialisation des variables d'instance
        self.all_packages: List[Dict[str, Any]] = []
        self.excluded_packages: List[str] = self.parent.settings.get("excluded_packages", [])
        self.selected_packages: set[str] = set()
        self.update_in_progress: bool = False
        
        # Créer les widgets
        self.create_widgets()
        
        # Centrer la fenêtre
        self.center_window()
        
        # Vérifier les mises à jour
        self.check_for_updates()
        
    def tr(self, key: str) -> str:
        """Get translation for key"""
        return self.parent.translations.get(key, key)
        
    def create_widgets(self):
        """Crée les widgets de la fenêtre des mises à jour"""
        # Frame principal avec scrollbar
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Boutons supérieurs
        button_frame = ctk.CTkFrame(self.main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Bouton de vérification des mises à jour
        self.check_button = ctk.CTkButton(
            button_frame,
            text=self.tr("check_updates"),
            command=self.check_for_updates,
            fg_color="#FF4B1F",
            hover_color="#FF6B47"
        )
        self.check_button.pack(side="left", padx=5)
        
        # Bouton d'installation
        self.install_button = ctk.CTkButton(
            button_frame,
            text=self.tr("install_updates"),
            command=self.install_selected_updates,
            state="disabled",
            fg_color="#808080",
            hover_color="#A0A0A0"
        )
        self.install_button.pack(side="left", padx=5)
        
        # Case à cocher "Tout sélectionner"
        self.select_all_var = ctk.BooleanVar(value=False)
        self.select_all_check = ctk.CTkCheckBox(
            button_frame,
            text=self.tr("select_all"),
            variable=self.select_all_var,
            command=self.toggle_all_packages,
            fg_color="#FF4B1F",
            hover_color="#FF6B47"
        )
        self.select_all_check.pack(side="left", padx=20)
        
        # Boutons des pilotes
        driver_frame = ctk.CTkFrame(button_frame)
        driver_frame.pack(side="right")
        
        # Bouton AMD
        self.amd_button = ctk.CTkButton(
            driver_frame,
            text=self.tr("download_amd_drivers"),
            command=self.download_amd_drivers,
            fg_color="#808080",
            hover_color="#A0A0A0"
        )
        self.amd_button.pack(side="left", padx=5)
        
        # Bouton Framework
        self.framework_button = ctk.CTkButton(
            driver_frame,
            text=self.tr("framework_drivers"),
            command=self.open_framework_drivers,
            fg_color="#808080",
            hover_color="#A0A0A0"
        )
        self.framework_button.pack(side="left", padx=5)
        
        # Frame pour la liste des paquets avec en-têtes
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # En-têtes
        headers_frame = ctk.CTkFrame(list_frame)
        headers_frame.pack(fill="x", padx=5, pady=5)
        
        headers = [
            ("", 30),  # Pour la checkbox
            ("package_name", 170),
            ("current_version", 100),
            ("latest_version", 100),
            ("source", 80),
            ("status", 100),
            ("actions", 100)
        ]
        
        for header, width in headers[1:]:  # Skip the checkbox column
            label = ctk.CTkLabel(
                headers_frame,
                text=self.tr(header),
                width=width,
                anchor="w"
            )
            label.pack(side="left", padx=5)
        
        # Liste des paquets avec scrollbar
        self.package_list = ctk.CTkScrollableFrame(list_frame)
        self.package_list.pack(fill="both", expand=True, padx=5)
        
        # Journal des mises à jour
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="x", pady=(10, 0))
        
        log_label = ctk.CTkLabel(
            log_frame,
            text=self.tr("update_log"),
            anchor="w"
        )
        log_label.pack(anchor="w", padx=5, pady=5)
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=100,
            wrap="word"
        )
        self.log_text.pack(fill="x", padx=5, pady=5)
        
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def log_message(self, message: str):
        """Ajoute un message au journal"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        
    def check_for_updates(self):
        """Vérifie les mises à jour disponibles et affiche tous les paquets installés"""
        def check():
            try:
                self.check_button.configure(state="disabled")
                self.log_message(self.tr("scanning_packages"))
                
                # Nettoyer la liste existante
                for widget in self.package_list.winfo_children():
                    widget.destroy()
                
                # Liste temporaire pour stocker tous les paquets
                self.all_packages = []
                
                # Vérifier les paquets pip
                self.check_pip_updates()
                
                # Vérifier les paquets winget
                self.check_winget_updates()
                
                # Vérifier la mise à jour de l'application
                self.check_app_update()
                
                # Trier et afficher les paquets
                self.all_packages.sort(key=lambda x: (x['status'] != self.tr("update_available"), x['name'].lower()))
                for pkg in self.all_packages:
                    self.add_package_to_list(**pkg)
                
                # Compter les mises à jour disponibles
                updates_available = sum(1 for pkg in self.all_packages if pkg['status'] == self.tr("update_available"))
                
                self.check_button.configure(state="normal")
                self.log_message(self.tr("scan_complete").format(
                    len(self.all_packages),
                    updates_available
                ))
                
            except Exception as e:
                logger.error(f"Erreur lors de la vérification des mises à jour: {e}")
                self.log_message(f"{self.tr('error_checking')}: {str(e)}")
                self.check_button.configure(state="normal")
        
        threading.Thread(target=check, daemon=True).start()
        
    def check_pip_updates(self):
        """Vérifie les mises à jour pip disponibles"""
        try:
            if getattr(sys, 'frozen', False):
                # Version exe - utiliser le fichier requirements.txt
                requirements_path = os.path.join(os.path.dirname(sys.executable), 'requirements.txt')
                if os.path.exists(requirements_path):
                    with open(requirements_path, 'r') as f:
                        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    
                    for req in requirements:
                        name = req.split('>=')[0].split('==')[0].strip()
                        if name.lower() in self.excluded_packages:
                            continue
                            
                        try:
                            # Obtenir la version installée depuis pkg_resources
                            dist = pkg_resources.get_distribution(name)
                            current_version = dist.version
                            
                            # Obtenir la dernière version depuis PyPI
                            latest_version = self.get_latest_pip_version(name)
                            if latest_version:
                                status = self.tr("update_available") if latest_version != current_version else self.tr("up_to_date")
                                self.all_packages.append({
                                    'name': name,
                                    'current_version': current_version,
                                    'latest_version': latest_version,
                                    'source': "pip",
                                    'status': status
                                })
                        except Exception as e:
                            logger.error(f"Erreur version pip pour {name}: {e}")
            else:
                # Version développement - utiliser pip list
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                installed_packages = json.loads(result.stdout)
                for package in installed_packages:
                    name = package['name']
                    if name.lower() in self.excluded_packages:
                        continue
                    
                    current_version = package['version']
                    try:
                        latest_version = self.get_latest_pip_version(name)
                        if latest_version:
                            status = self.tr("update_available") if latest_version != current_version else self.tr("up_to_date")
                            self.all_packages.append({
                                'name': name,
                                'current_version': current_version,
                                'latest_version': latest_version,
                                'source': "pip",
                                'status': status
                            })
                    except Exception as e:
                        logger.error(f"Erreur version pip pour {name}: {e}")
                        
        except Exception as e:
            logger.error(f"Erreur pip: {e}")
            self.log_message(f"Erreur pip: {str(e)}")
            
    def get_latest_pip_version(self, package_name: str) -> Optional[str]:
        """Obtient la dernière version d'un paquet pip"""
        try:
            response = requests.get(
                f"https://pypi.org/pypi/{package_name}/json",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()["info"]["version"]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la version de {package_name}: {e}")
        return None
        
    def check_winget_updates(self):
        """Vérifie les mises à jour winget disponibles"""
        try:
            if not self._is_winget_available():
                self.log_message("Winget n'est pas disponible sur ce système")
                return

            # Commande PowerShell améliorée
            ps_command = """
            $ProgressPreference = 'SilentlyContinue'
            $ErrorActionPreference = 'SilentlyContinue'
            
            # Accepter les accords de source
            winget list --accept-source-agreements | Out-Null
            
            # Obtenir la liste des paquets installés
            $installed = winget list --disable-interactivity | Out-String
            
            # Obtenir la liste des mises à jour disponibles
            $updates = winget upgrade --include-unknown --disable-interactivity | Out-String
            
            # Convertir en format structuré
            $installedLines = $installed -split "`n" | Where-Object { $_ -match '\\S' }
            $updateLines = $updates -split "`n" | Where-Object { $_ -match '\\S' }
            
            # Créer un objet JSON
            $result = @{
                'installed' = $installedLines
                'updates' = $updateLines
            }
            
            # Convertir en JSON et retourner
            $result | ConvertTo-Json -Depth 10
            """

            # Exécuter la commande PowerShell avec des privilèges élevés
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            try:
                data = json.loads(result.stdout)
                installed_lines = data['installed']
                update_lines = data['updates']
                
                # Trouver l'index des en-têtes
                header_index = -1
                for i, line in enumerate(installed_lines):
                    if any(header in line for header in ["Name", "Nom", "Id"]):
                        header_index = i
                        break
                
                if header_index >= 0:
                    # Parser les paquets installés
                    for line in installed_lines[header_index + 2:]:
                        if line.strip() and not line.startswith("-"):
                            # Utiliser une expression régulière plus robuste pour le parsing
                            parts = [p.strip() for p in re.split(r'\s{2,}|\t+', line)]
                            if len(parts) >= 2:
                                name = parts[0]
                                current_version = parts[1] if len(parts) > 1 else ""
                                
                                # Ignorer les lignes d'en-tête et de séparation
                                if name and not any(x in name.lower() for x in ["name", "nom", "id", "-"]):
                                    # Vérifier si une mise à jour est disponible
                                    update_available = False
                                    latest_version = current_version
                                    
                                    for update_line in update_lines:
                                        if name in update_line:
                                            update_parts = [p.strip() for p in re.split(r'\s{2,}|\t+', update_line)]
                                            if len(update_parts) >= 3:
                                                latest_version = update_parts[2]
                                                update_available = True
                                                break
                                    
                                    self.all_packages.append({
                                        'name': name,
                                        'current_version': current_version,
                                        'latest_version': latest_version,
                                        'source': "winget",
                                        'status': self.tr("update_available") if update_available else self.tr("up_to_date")
                                    })
                
                # Log pour le débogage
                logger.info(f"Paquets winget trouvés: {len([p for p in self.all_packages if p['source'] == 'winget'])}")
                
            except Exception as e:
                logger.error(f"Erreur parsing winget: {e}")
                self.log_message(f"Erreur parsing winget: {str(e)}")
                
        except Exception as e:
            logger.error(f"Erreur winget: {e}")
            self.log_message(f"Erreur winget: {str(e)}")
            
    def _is_winget_available(self) -> bool:
        """Vérifie si winget est disponible"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Command winget"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
        
    def check_app_update(self):
        """Vérifie la mise à jour de l'application"""
        try:
            response = requests.get(
                "https://api.github.com/repos/yourusername/framework-mini-hub/releases/latest",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data["tag_name"].replace("v", "")
                current_version = self.parent.version
                
                if latest_version > current_version:
                    self.all_packages.append({
                        'name': "Framework Mini Hub",
                        'current_version': current_version,
                        'latest_version': latest_version,
                        'source': "github",
                        'status': self.tr("update_available")
                    })
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la mise à jour de l'application: {e}")
            
    def add_package_to_list(self, name: str, current_version: str, latest_version: str,
                           source: str, status: str):
        """Ajoute un paquet à la liste"""
        # Frame pour le paquet
        package_frame = ctk.CTkFrame(self.package_list)
        package_frame.pack(fill="x", padx=5, pady=2)
        
        # Case à cocher (désactivée si le paquet est à jour)
        var = ctk.BooleanVar(value=False)
        check = ctk.CTkCheckBox(
            package_frame,
            text="",
            variable=var,
            command=lambda: self.toggle_package(name, var.get()),
            width=30,
            fg_color="#FF4B1F",
            hover_color="#FF6B47",
            state="normal" if status == self.tr("update_available") else "disabled"
        )
        check.pack(side="left", padx=5)
        
        # Couleur de fond selon le statut
        bg_color = "#1E1E1E" if status == self.tr("update_available") else "#2A2A2A"
        package_frame.configure(fg_color=bg_color)
        
        # Informations du paquet
        ctk.CTkLabel(
            package_frame,
            text=name,
            width=170,
            anchor="w"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            package_frame,
            text=current_version,
            width=100,
            anchor="w"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            package_frame,
            text=latest_version,
            width=100,
            anchor="w"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            package_frame,
            text=source,
            width=80,
            anchor="w"
        ).pack(side="left", padx=5)
        
        # Status avec couleur
        status_color = "#FF4B1F" if status == self.tr("update_available") else "#808080"
        ctk.CTkLabel(
            package_frame,
            text=status,
            width=100,
            anchor="w",
            text_color=status_color
        ).pack(side="left", padx=5)
        
        # Bouton d'exclusion
        exclude_btn = ctk.CTkButton(
            package_frame,
            text=self.tr("exclude_package") if name not in self.excluded_packages else self.tr("include_package"),
            command=lambda: self.toggle_package_exclusion(name),
            width=100,
            fg_color="#808080",
            hover_color="#A0A0A0"
        )
        exclude_btn.pack(side="left", padx=5)
        
        # Activer le bouton d'installation seulement s'il y a des mises à jour disponibles
        if status == self.tr("update_available"):
            self.install_button.configure(state="normal")
        
    def toggle_package(self, package_name: str, selected: bool):
        """Gère la sélection/désélection d'un paquet"""
        if selected:
            self.selected_packages.add(package_name)
        else:
            self.selected_packages.discard(package_name)
            self.select_all_var.set(False)
            
        # Mettre à jour l'état du bouton d'installation
        self.install_button.configure(
            state="normal" if self.selected_packages else "disabled"
        )
        
    def toggle_all_packages(self):
        """Sélectionne ou désélectionne tous les paquets qui ont des mises à jour disponibles"""
        select_all = self.select_all_var.get()
        
        # Mettre à jour la liste des paquets sélectionnés
        self.selected_packages.clear()
        
        for widget in self.package_list.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                checkbox = widget.winfo_children()[0]
                if isinstance(checkbox, ctk.CTkCheckBox):
                    # Vérifier si le paquet a une mise à jour disponible
                    status_label = None
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel) and child.cget("text_color") == "#FF4B1F":
                            status_label = child
                            break
                    
                    if status_label and status_label.cget("text") == self.tr("update_available"):
                        if select_all:
                            checkbox.select()
                            # Ajouter le paquet à la liste des sélectionnés
                            name_label = widget.winfo_children()[1]
                            self.selected_packages.add(name_label.cget("text"))
                        else:
                            checkbox.deselect()
                    else:
                        checkbox.deselect()  # Toujours désélectionner les paquets à jour
        
        # Mettre à jour l'état du bouton d'installation
        self.install_button.configure(
            state="normal" if self.selected_packages else "disabled"
        )
        
    def toggle_package_exclusion(self, package_name: str):
        """Ajoute ou retire un paquet de la liste d'exclusion"""
        if package_name in self.excluded_packages:
            self.excluded_packages.remove(package_name)
            self.log_message(f"{package_name} {self.tr('remove_from_exclusions')}")
        else:
            self.excluded_packages.append(package_name)
            self.log_message(f"{package_name} {self.tr('excluded')}")
            
        # Sauvegarder la liste d'exclusion
        self.parent.settings["excluded_packages"] = self.excluded_packages
        self.parent.save_settings()
        
        # Rafraîchir la liste
        self.check_for_updates()
        
    def install_selected_updates(self):
        """Installe les mises à jour sélectionnées"""
        def install():
            try:
                self.update_in_progress = True
                self.install_button.configure(state="disabled")
                self.check_button.configure(state="disabled")
                
                for package_name in self.selected_packages:
                    try:
                        # Trouver le widget du paquet
                        for widget in self.package_list.winfo_children():
                            if isinstance(widget, ctk.CTkFrame):
                                name_label = widget.winfo_children()[1]
                                if name_label.cget("text") == package_name:
                                    source_label = widget.winfo_children()[4]
                                    source = source_label.cget("text")
                                    
                                    self.log_message(f"{self.tr('installing')} {package_name}...")
                                    
                                    if source == "pip":
                                        subprocess.run(
                                            [sys.executable, "-m", "pip", "install", "-U", package_name],
                                            check=True
                                        )
                                    elif source == "winget":
                                        subprocess.run(
                                            ["winget", "upgrade", package_name],
                                            check=True
                                        )
                                    elif source == "github":
                                        self.install_app_update()
                                        
                                    self.log_message(f"{package_name} {self.tr('update_complete')}")
                                    break
                                    
                    except Exception as e:
                        logger.error(f"Erreur lors de l'installation de {package_name}: {e}")
                        self.log_message(f"{self.tr('error_installing')} {package_name}: {str(e)}")
                        
                self.update_in_progress = False
                self.install_button.configure(state="normal")
                self.check_button.configure(state="normal")
                self.check_for_updates()
                
            except Exception as e:
                logger.error(f"Erreur lors de l'installation des mises à jour: {e}")
                self.log_message(f"{self.tr('error_installing')}: {str(e)}")
                self.update_in_progress = False
                self.install_button.configure(state="normal")
                self.check_button.configure(state="normal")
                
        threading.Thread(target=install, daemon=True).start()
        
    def install_app_update(self):
        """Installe la mise à jour de l'application"""
        try:
            self.log_message(self.tr("downloading"))
            
            response = requests.get(
                "https://api.github.com/repos/yourusername/framework-mini-hub/releases/latest",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                download_url = data["assets"][0]["browser_download_url"]
                
                # Télécharger le fichier
                update_file = Path("update.exe")
                response = requests.get(download_url, stream=True)
                
                with open(update_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                self.log_message(self.tr("installing"))
                
                # Lancer l'installateur et fermer l'application
                subprocess.Popen([str(update_file)])
                self.parent.quit_app()
                
        except Exception as e:
            logger.error(f"Erreur lors de l'installation de la mise à jour de l'application: {e}")
            raise
            
    def download_amd_drivers(self):
        """Télécharge les pilotes AMD"""
        try:
            # Ouvrir la page de téléchargement des pilotes AMD
            webbrowser.open("https://www.amd.com/en/support")
            self.log_message(self.tr("download_amd_drivers"))
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de la page des pilotes AMD: {e}")
            self.log_message(f"{self.tr('error')}: {str(e)}")
            
    def open_framework_drivers(self):
        """Ouvre la page des pilotes Framework"""
        try:
            # Ouvrir la page des pilotes Framework
            webbrowser.open("https://knowledgebase.frame.work/fr/telechargements-du-bios-et-des-pilotes-rJ3PaCexh")
            self.log_message(self.tr("framework_drivers"))
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de la page des pilotes Framework: {e}")
            self.log_message(f"{self.tr('error')}: {str(e)}")
            
    def update_ui_language(self):
        """Met à jour l'interface avec la nouvelle langue"""
        try:
            # Mettre à jour le titre de la fenêtre
            self.title(self.tr("updates"))
            
            # Mettre à jour les boutons
            self.check_button.configure(text=self.tr("check_updates"))
            self.install_button.configure(text=self.tr("install_updates"))
            self.select_all_check.configure(text=self.tr("select_all"))
            self.amd_button.configure(text=self.tr("download_amd_drivers"))
            self.framework_button.configure(text=self.tr("framework_drivers"))
            
            # Rafraîchir la liste des paquets
            self.check_for_updates()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la langue: {e}") 