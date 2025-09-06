# Serveur MCP LaTeX - Installation Windows
This MCP server python-based code is designed for LaTeX users looking for more AI integration

## 📍 Emplacements sur votre système

- **Serveur MCP** : `C:\Users\username\Documents\MCP\latex-server\`
- **Projets LaTeX** : `C:\Users\username\Documents\LaTeX\`
- **Config Claude** : `C:\Users\username\AppData\Roaming\Claude\claude_desktop_config.json`

## ⚡ Installation manuelle

1. **Créer les dossiers** :
```cmd
mkdir C:\Users\username\Documents\MCP\latex-server
mkdir C:\Users\username\Documents\LaTeX
```

2. **Installer les dépendances** :
```cmd
cd C:\Users\username\Documents\MCP\latex-server
pip install mcp aiofiles
```

3. **Copier le serveur** :
- Placez `mcp_latex_server.py` dans `C:\Users\username\Documents\MCP\latex-server\`

4. **Configurer Claude Desktop** :
- Éditez `C:\Users\username\AppData\Roaming\Claude\claude_desktop_config.json`
- Ajoutez :
```json
{
  "mcpServers": {
    "latex-server": {
      "command": "python",
      "args": [
        "C:\\Users\\username\\Documents\\MCP\\latex-server\\mcp_latex_server.py",
        "--workspace",
        "C:\\Users\\username\\Documents\\LaTeX"
      ]
    }
  }
}
```

5. **Redémarrer Claude Desktop**

## ✅ Vérification

### Test rapide dans Claude Desktop

Tapez dans Claude :
```
"Crée un fichier test.tex avec un template article"
```

Si ça fonctionne, Claude créera `C:\Users\username\Documents\LaTeX\test.tex`

### Test en ligne de commande

```cmd
cd C:\Users\username\Documents\MCP\latex-server
python mcp_latex_server.py --workspace C:\Users\username\Documents\LaTeX
```

## 📂 Structure finale

```
C:\Users\username\
├── Documents\
│   ├── MCP\
│   │   └── latex-server\
│   │       ├── mcp_latex_server.py      # Serveur principal
│   │       └── README.md                 # Ce fichier
│   │
│   └── LaTeX\                           # Vos projets
│       ├── Articles\
│       ├── Presentations\
│       └── (vos fichiers .tex)
│
└── AppData\
    └── Roaming\
        └── Claude\
            └── claude_desktop_config.json  # Configuration
```

## 🎯 Utilisation quotidienne

### Commandes essentielles dans Claude

| Action | Commande dans Claude |
|--------|---------------------|
| Créer un document | `"Crée article.tex avec template article"` |
| Lire un fichier | `"Lis mon fichier thesis.tex"` |
| Compiler | `"Compile main.tex avec pdflatex"` |
| Valider | `"Vérifie la syntaxe de document.tex"` |
| Organiser | `"Organise mes fichiers LaTeX"` |
| Nettoyer | `"Nettoie les fichiers auxiliaires"` |
| Changer de répertoire | `"Change le répertoire de travail pour ..."` |

### Workflows recommandés

**Nouvel article :**
1. `"Crée un article sur l'IA avec support mathématique"`
2. `"Compile l'article"`

**Projet existant :**
1. Copiez votre projet dans `C:\Users\username\Documents\LaTeX\mon-projet\`
2. `"Liste les fichiers dans mon-projet"`
3. `"Compile mon-projet/main.tex"`

## 🔧 Dépannage

### Le serveur ne se charge pas
- Vérifiez que Claude Desktop est bien fermé puis relancé
- Vérifiez le fichier de config JSON (attention aux virgules et guillemets)

### Erreur "python non reconnu"
- Ajoutez Python au PATH système
- Ou utilisez le chemin complet : `"command": "C:\\Python312\\python.exe"`
- Si l'erreur persiste, optez pour un environnement virtuel et ajouter le PATH dans la config JSON 

### Erreur de compilation LaTeX
- Vérifiez que MiKTeX ou TeX Live est installé
- Testez `pdflatex --version` dans cmd

## 📞 Support

- Logs : Dans Claude Desktop, Ctrl+Shift+I → Console
- Test : `mcp_latex_server.py` dans le dossier du serveur
- Debug : Ajoutez `"--log-level", "DEBUG"` dans les args de la config JSON

---

*Serveur MCP LaTeX v1.0.0*  
*Chemin serveur : C:\Users\username\Documents\MCP\latex-server*  
*Workspace LaTeX : C:\Users\username\Documents\LaTeX*
