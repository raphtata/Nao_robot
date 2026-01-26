# Installation de Python 2.7 pour NAOqi

## 📥 Téléchargement de Python 2.7

### ⚠️ IMPORTANT: Utilisez la version 32-bit

Le SDK NAOqi de Choregraphe nécessite Python 2.7 **32-bit** (même sur Windows 64-bit).

### Option 1: Site officiel Python (Recommandé)
1. Téléchargez Python 2.7.18 **32-bit**:
   - **Lien direct (32-bit)**: https://www.python.org/ftp/python/2.7.18/python-2.7.18.msi
   - ❌ NE PAS utiliser la version amd64 (64-bit)

2. Lancez l'installateur MSI

3. **IMPORTANT**: Pendant l'installation:
   - Choisissez "Install for all users" ou "Just for me"
   - Notez le chemin d'installation (par défaut: `C:\Python27\`)
   - **Cochez "Add python.exe to Path"** (optionnel mais pratique)
   
4. Si vous avez déjà installé Python 2.7 64-bit:
   - Désinstallez-le d'abord (Panneau de configuration → Programmes)
   - Puis installez la version 32-bit

### Option 2: Chocolatey (si vous l'utilisez)
```bash
choco install python2
```

## 🔧 Vérification de l'installation

Ouvrez un nouveau terminal PowerShell et testez:

```bash
C:\Python27\python.exe --version
```

Vous devriez voir: `Python 2.7.18`

## 📝 Chemins d'installation typiques

- Installation standard: `C:\Python27\python.exe`
- Chocolatey: `C:\Python27\python.exe`
- Installation utilisateur: `C:\Users\<votre_nom>\AppData\Local\Programs\Python\Python27\python.exe`

## ✅ Après l'installation

Une fois Python 2.7 installé, lancez simplement:

```bash
.\run_python27.bat
```

Ce script utilisera automatiquement Python 2.7 avec le SDK NAOqi local du dossier `lib/`.

## ⚠️ Notes importantes

- Python 2.7 n'est plus maintenu depuis 2020, mais il est nécessaire pour NAOqi
- N'utilisez Python 2.7 QUE pour ce projet NAO
- Gardez Python 3.12 pour vos autres projets
- Les deux versions peuvent coexister sans problème
