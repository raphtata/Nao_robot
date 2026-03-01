# Projet Kinect 360 -> NAO (Windows)

Ce sous-projet est **entièrement isolé** dans `projet_kinect/`.

## Objectif

1. Capturer le flux RGB de la **Kinect 360** (1ère génération)
2. Extraire un squelette (haut du corps) avec **MediaPipe Pose**
3. Envoyer les articulations en UDP (JSON)
4. Piloter **NAO** en temps réel via NAOqi

## Prérequis

- **Kinect SDK v1.8** installé (fournit les drivers USB pour la Kinect 360)
- **Python 3.10+** (venv du projet) pour le streamer Kinect et le viewer Streamlit
- **Python 2.7 32-bit** + **NAOqi SDK** pour le script NAO mirror

## Architecture

```
Kinect 360 (USB)
    |
    v
kinect360_real_streamer.py  (Python 3 - OpenCV + MediaPipe)
    |
    |--- UDP :5006 ---> nao_mirror_py27.py  (Python 2.7 - NAOqi)
    |--- UDP :5007 ---> skeleton_streamlit_app.py  (Python 3 - Streamlit)
```

### Fichiers

| Fichier | Rôle |
|---|---|
| `src/kinect360_real_streamer.py` | Capture Kinect RGB via OpenCV (DirectShow), extraction squelette MediaPipe, envoi UDP |
| `src/kinect_mock_streamer.py` | Squelette simulé (pour tester le pipeline sans Kinect) |
| `src/nao_mirror_py27.py` | Réception UDP, conversion angles, pilotage NAO (Python 2.7) |
| `src/skeleton_streamlit_app.py` | Visualisation temps réel du squelette (Streamlit) |
| `src/mapping.py` | Conversion squelette → angles NAO + limites de sécurité |
| `src/config.py` | Chargement `.env` |
| `src/detect_cameras.py` | Détecte les caméras disponibles et leur index OpenCV |

## Installation

```powershell
cd projet_kinect
..\venv\Scripts\activate
pip install -r requirements.txt
```

### Modèle MediaPipe (Python 3.12+)

Si MediaPipe utilise le backend `tasks` (Python 3.12), télécharger le modèle :

```
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

Placer dans `projet_kinect/models/` et définir `POSE_MODEL_PATH` dans `.env`.

## Configuration

1. Copier `.env.example` → `.env`
2. Détecter l'index caméra Kinect :
   ```powershell
   python src\detect_cameras.py
   ```
3. Mettre `CAMERA_INDEX` dans `.env` (par défaut `0`)
4. Ajuster `NAO_IP`, `NAO_PORT`, `CHOREGRAPHE_BIN` si besoin

### Variables `.env`

| Variable | Description | Défaut |
|---|---|---|
| `UDP_HOST` | Adresse d'écoute | `127.0.0.1` |
| `UDP_PORT` | Port UDP pour NAO mirror | `5006` |
| `UDP_PORT_VIEWER` | Port UDP pour Streamlit viewer | `5007` |
| `FPS` | Images/seconde | `20` |
| `CAMERA_INDEX` | Index OpenCV de la Kinect | `0` |
| `SHOW_PREVIEW` | Afficher la preview OpenCV | `1` |
| `POSE_MODEL_PATH` | Chemin vers `pose_landmarker_full.task` | (auto) |
| `NAO_IP` | IP du robot NAO | `169.254.201.219` |
| `NAO_PORT` | Port NAOqi | `9559` |
| `CHOREGRAPHE_BIN` | Dossier bin de Choregraphe | *(voir .env.example)* |

## Lancer

### Lancement complet (3 terminaux)

**Terminal 1** — NAO mirror (Python 2.7) :
```powershell
C:\Python27\python.exe projet_kinect\src\nao_mirror_py27.py
```

**Terminal 2** — Kinect streamer (Python 3) :
```powershell
python projet_kinect\src\kinect360_real_streamer.py
```

**Terminal 3** — Streamlit viewer :
```powershell
streamlit run projet_kinect\src\skeleton_streamlit_app.py --server.port 8502
```

Ouvrir http://localhost:8502

### Lancement via batch

```powershell
.\projet_kinect\run_kinect_real.bat
```

### Mode mock (sans Kinect)

Remplacer le Terminal 2 par :
```powershell
python projet_kinect\src\kinect_mock_streamer.py
```

## Comment ça marche

1. Le **Kinect SDK v1.8** expose la caméra RGB comme un périphérique DirectShow standard
2. **OpenCV** capture les frames via `cv2.VideoCapture(index, cv2.CAP_DSHOW)`
3. **MediaPipe Pose** extrait 33 landmarks du corps
4. Le streamer envoie les 8 joints du haut du corps (tête, cou, épaules, coudes, poignets) en JSON/UDP
5. Le NAO mirror convertit les joints en angles NAO (10 DOF : tête + bras) et les applique via `ALMotion.setAngles`
