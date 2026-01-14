# Installation du SDK NAOqi pour Python

Le SDK NAOqi n'est **pas disponible via pip**. Vous devez le télécharger et l'installer manuellement.

## 📥 Téléchargement du SDK

### Option 1: Site officiel Aldebaran/SoftBank Robotics

1. Visitez: https://community-static.aldebaran.com/resources/
2. Cherchez "Python SDK" ou "pynaoqi"
3. Téléchargez la version correspondant à votre système:
   - **Windows 64-bit + Python 2.7**: `pynaoqi-python2.7-2.8.7.4-win64-vs2015.zip`
   - **Windows 64-bit + Python 3.6**: `pynaoqi-python3.6-2.8.7.4-win64-vs2015.zip`

### Option 2: Archive GitHub (communauté)

Certains utilisateurs ont archivé le SDK sur GitHub. Recherchez "pynaoqi" sur GitHub.

## 🔧 Installation

### Méthode 1: Installation dans le projet (Recommandé)

1. **Extraire le SDK**
   ```
   Extraire le fichier .zip téléchargé
   Vous obtiendrez un dossier comme: pynaoqi-python2.7-2.8.7.4-win64-vs2015/
   ```

2. **Copier les fichiers dans votre projet**
   ```
   Copiez tous les fichiers du dossier lib/ du SDK vers:
   C:\Users\rafta\CascadeProjects\windsurf-project-2\
   
   Fichiers à copier:
   - naoqi.py
   - _qi.pyd (ou _qi.so sur Linux)
   - qi.pyd (ou qi.so sur Linux)
   - Et tous les autres fichiers .pyd/.dll
   ```

3. **Tester l'installation**
   ```bash
   python -c "import naoqi; print('SDK installé!')"
   ```

### Méthode 2: Ajouter le chemin dans le script

1. **Extraire le SDK** quelque part sur votre disque

2. **Modifier le script** `nao_speak_simple.py`:
   ```python
   import sys
   # Remplacez par le chemin réel vers le dossier lib du SDK
   sys.path.append("C:/chemin/vers/pynaoqi-python2.7-2.8.7.4-win64-vs2015/lib")
   
   from naoqi import ALProxy
   ```

### Méthode 3: Installation système (PYTHONPATH)

1. **Extraire le SDK**

2. **Ajouter au PYTHONPATH**
   
   **Windows (PowerShell):**
   ```powershell
   $env:PYTHONPATH = "C:\chemin\vers\pynaoqi\lib"
   ```
   
   **Windows (Permanent):**
   - Panneau de configuration → Système → Paramètres système avancés
   - Variables d'environnement
   - Ajouter `PYTHONPATH` avec le chemin vers le dossier `lib`

## ⚠️ Problèmes courants

### Python 3.8+ non supporté

Le SDK officiel NAOqi ne supporte que Python 2.7 et Python 3.6/3.7 maximum.

**Solutions:**
1. Utilisez Python 3.7 ou inférieur
2. Créez un environnement virtuel avec Python 3.7:
   ```bash
   py -3.7 -m venv venv37
   venv37\Scripts\activate
   ```

### Erreur "DLL load failed"

Sur Windows, vous pourriez avoir besoin de:
1. Visual C++ Redistributable 2015-2019
2. Téléchargez depuis: https://aka.ms/vs/16/release/vc_redist.x64.exe

### Le module naoqi n'est pas trouvé

Vérifiez:
1. Que vous avez bien copié **tous** les fichiers du SDK
2. Que le chemin dans `sys.path.append()` est correct
3. Que vous utilisez la bonne version de Python (2.7 ou 3.6/3.7)

## 🚀 Utilisation après installation

Une fois le SDK installé, lancez:

```bash
python nao_speak_simple.py
```

Le script devrait se connecter au robot et le faire parler!

## 📚 Documentation

- [Documentation NAOqi Python SDK](http://doc.aldebaran.com/2-8/dev/python/index.html)
- [API ALTextToSpeech](http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech.html)
