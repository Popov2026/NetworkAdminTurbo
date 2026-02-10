# NetworkAdminTurbo By Popov © 2026
Network Admin Turbo est un outil d'administration réseau léger et performant écrit en Python gratuit. Il permet de surveiller en temps réel l'état de présence (UP/DOWN) des équipements d'un parc informatique, de découvrir de nouveaux périphériques et de gérer une base de données d'inventaire simple via une interface graphique moderne.


✨ Fonctionnalités principales
Scan Multi-threadé : Utilisation de ThreadPoolExecutor pour scanner jusqu'à 254 adresses IP en quelques secondes.

Inventaire Dynamique : Gestion d'un fichier texte (liste_auto.txt) regroupant NOM, IP et adresse MAC.

Tri Intelligent (Cyclique) :

Tri par Nom, IP ou adresse MAC.

Mise en avant (Priorisation) des équipements en ligne (Online 1er) ou hors ligne (Offline 1er) sans masquer le reste du parc.

Découverte de Nouveaux Équipements : Identification automatique des machines présentes sur le réseau mais non répertoriées dans votre liste, avec option d'ajout rapide en un clic (+).

Automatisation :

Scan automatique programmable (intervalle en minutes).

Auto-scan intelligent déclenché automatiquement 3 secondes après un ajout ou 2 secondes après un changement de tri.

Persistance & Sécurité :

Sauvegarde automatique des paramètres (IP, fichier, délais) dans un fichier config.ini.

Système d'archivage automatique des listes à chaque scan dans un dossier backups.

Interface Moderne : UI basée sur CustomTkinter avec mode sombre (Dark Mode) natif et rafraîchissement atomique pour une stabilité visuelle parfaite.

🔍 Zoom technique : Fonctionnement du Scan
Le script n'utilise pas uniquement le protocole ICMP (Ping). Il combine plusieurs méthodes pour obtenir un maximum d'informations de manière asynchrone :

Vérification de présence (ICMP) : Un ping rapide est envoyé à l'adresse cible. Pour optimiser la vitesse, le délai d'attente (timeout) est réduit et le script utilise un ThreadPoolExecutor pour traiter 100 adresses simultanément.

Résolution de nom (DNS Local) : Si l'hôte répond, le script tente une résolution de nom inversée via socket.gethostbyaddr pour récupérer le nom d'hôte (Hostname) configuré sur le réseau.

Récupération de l'adresse MAC (ARP) : L'adresse MAC n'est pas transmise par le ping. Le script interroge dynamiquement la table ARP (Address Resolution Protocol) de votre système d'exploitation à l'aide de la commande arp -a. Il utilise ensuite une expression régulière (Regex) pour extraire l'adresse physique formatée.

Le scan est conçu pour être "non-intrusif" : l'interface utilisateur est totalement reconstruite une fois le scan terminé pour éviter les clignotements et les conflits d'affichage pendant la récupération des données.

🛠️ Installation et Dépendances
Le script nécessite Python 3.10+.

1. Cloner le projet
Bash
git clone https://github.com/popov2026/NetworkAdminTurbo.git
cd NetworkAdminTurbo
2. Installer les bibliothèques Python
L'interface graphique utilise CustomTkinter. Les autres modules utilisés (os, subprocess, threading, socket, configparser) font partie de la bibliothèque standard de Python.

Installez la dépendance principale via pip :

Bash
pip install customtkinter
3. Prérequis système
Windows : Le script est optimisé pour Windows (gestion des flags de création de processus pour éviter les fenêtres CMD intempestives lors du ping).

Privilèges : Aucun privilège administrateur n'est requis pour le ping standard, mais assurez-vous que votre pare-feu autorise les requêtes ICMP sortantes.

🚀 Utilisation
Lancez le script : python NetworkAdminTurbo_1.5.pyw

Configuration : Renseignez votre préfixe réseau (ex: 192.168.1.), la plage d'IP à scanner (ex: de 1 à 254) et sélectionnez votre fichier de liste.

Scan : Cliquez sur "LANCER SCAN TURBO" pour rafraîchir l'état du parc.

Gestion :

Cliquez sur le Nom d'un appareil pour le renommer.

Cliquez sur la croix X rouge pour supprimer un appareil.

Utilisez les boutons de TRI en haut à droite pour organiser votre vue.

📂 Structure des fichiers
NetworkAdminTurbo_1.5.pyw : Le script principal.

config.ini : Stocke vos préférences de scan (généré automatiquement).

liste_auto.txt : Votre base de données d'équipements (format CSV).

backups/ : Dossier contenant les sauvegardes datées de vos listes.

📝 Licence
Ce projet est destiné à un usage administratif et éducatif.
Copyright © 2026 Popov & Gemini - Tous droits réservés.
