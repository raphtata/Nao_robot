# Projet NAO V3 - Collection de Fonctionnalités

Collection de projets Python pour contrôler un robot NAO V3 avec différentes fonctionnalités: conversation vocale avec IA, suivi de visage, et gestes animés.

## 📋 Prérequis

- **Python 2.7 32-bit** (pour conversation vocale et SDK local)
- **Python 3.7** (pour suivi de visage avec OpenCV)
- Robot NAO V3 connecté en Ethernet
- Adresse IP du robot: `169.254.201.219`
- Choregraphe 2.8 installé (pour SDK NAOqi)

## 🎯 Projets Disponibles

### 1. 🗣️ Conversation Vocale avec Groq LLM
**Fichier:** `nao_voice_conversation_py27.py`  
**Script:** `run_voice_conversation.bat`

Système de conversation vocale intelligent utilisant:
- Microphone de NAO pour capturer la voix
- Groq Whisper API pour transcription audio
- Groq LLM (llama-3.3-70b-versatile) pour génération de réponses
- Animations de réflexion (grattage de tête)
- Hochement de tête pendant l'écoute

**Lancer:**
```bash
.\run_voice_conversation.bat
```

**Documentation complète:** `VOICE_CONVERSATION.md`

---

### 2. 👁️ Suivi de Visage avec Caméra NAO
**Fichier:** `nao_face_tracking_nao_camera.py`  
**Script:** `run_face_tracking_nao.bat`

Suivi de visage en temps réel utilisant:
- Caméra intégrée de NAO
- Module ALFaceDetection de NAOqi
- ALTracker pour mouvement automatique de la tête
- Détection et reconnaissance faciale

**Lancer:**
```bash
.\run_face_tracking_nao.bat
```

**Documentation complète:** `FACE_TRACKING_NAO_CAMERA.md`

---

### 3. 🤖 Gestes et Animations
**Fichier:** `nao_with_local_sdk.py`  
**Script:** `run_simple.bat`

Démonstrations de gestes animés:
- Salut de la main ("coucou")
- Grattage de tête avec parole
- Contrôle précis des articulations
- Stabilisation du robot pendant les mouvements

**Lancer:**
```bash
.\run_simple.bat
```

---

## 🚀 Installation

### Installation Python 2.7 (pour conversation vocale)

Voir le guide détaillé: `INSTALL_PYTHON27.md`

**Important:** Utilisez Python 2.7 **32-bit** uniquement!

### Installation SDK NAOqi

Voir le guide détaillé: `INSTALLATION_SDK.md`

Le SDK est déjà inclus dans le dossier `lib/` de ce projet.

### Installer les dépendances

**Pour conversation vocale:**
```bash
pip install -r requirements.txt
```

**Pour suivi de visage:**
```bash
pip install -r requirements_face_tracking.txt
```

## ⚙️ Configuration

### Fichier .env (Conversation Vocale)

Créez un fichier `.env` avec vos clés API Groq:

```bash
GROQ_API_KEY=votre_cle_api_groq
LLM_MODEL=llama-3.3-70b-versatile
```

### Paramètres de Conversation

Dans `nao_voice_conversation_py27.py`, vous pouvez ajuster:
- **Durée d'enregistrement:** `duration=5` (secondes)
- **Nombre d'échanges:** `num_exchanges=5`
- **Température LLM:** `temperature=0.7`
- **Max tokens:** `max_tokens=350`

### Changer l'adresse IP du robot

Si votre robot NAO a une adresse IP différente, modifiez la variable `NAO_IP` dans chaque script:

```python
NAO_IP = "169.254.201.219"  # Votre adresse IP
```

### Personnaliser les animations

Les angles des articulations peuvent être ajustés dans les fonctions d'animation:
- Positions en **radians** pour les articulations
- Positions en **0.0-1.0** pour RHand (ouverture de la main)
- Vitesse en **0.0-1.0** (fraction de vitesse maximale)

## 📝 Structure du Projet

```
windsurf-project-2/
├── 🗣️ Conversation Vocale
│   ├── nao_voice_conversation_py27.py    # Script principal (Python 2.7)
│   ├── run_voice_conversation.bat         # Lanceur Windows
│   ├── VOICE_CONVERSATION.md              # Documentation
│   └── .env                               # Configuration API Groq
│
├── 👁️ Suivi de Visage
│   ├── nao_face_tracking_nao_camera.py   # Suivi avec caméra NAO
│   ├── run_face_tracking_nao.bat         # Lanceur Windows
│   ├── FACE_TRACKING_NAO_CAMERA.md       # Documentation
│   └── requirements_face_tracking.txt     # Dépendances
│
├── 🤖 Gestes et Animations
│   ├── nao_with_local_sdk.py             # Gestes animés
│   └── run_simple.bat                     # Lanceur Windows
│
├── 📚 Documentation
│   ├── README.md                          # Ce fichier
│   ├── INSTALLATION_SDK.md                # Guide SDK NAOqi
│   └── INSTALL_PYTHON27.md                # Guide Python 2.7
│
├── 🔧 Configuration
│   ├── requirements.txt                   # Dépendances conversation
│   ├── requirements_face_tracking.txt     # Dépendances face tracking
│   └── .gitignore                         # Fichiers ignorés par Git
│
└── 📦 Ressources
    ├── lib/                               # SDK NAOqi local
    └── venv/                              # Environnement virtuel
```

## 🐛 Dépannage

### Erreur de connexion au robot

1. Vérifiez que le robot NAO est allumé (yeux bleus)
2. Vérifiez le câble Ethernet
3. Testez la connexion:
   ```bash
   ping 169.254.201.219
   ```
4. Configurez votre PC en réseau local (169.254.x.x)

### Erreur "DLL load failed" (Python 2.7)

**Cause:** Python 64-bit utilisé au lieu de 32-bit

**Solution:** Installez Python 2.7 **32-bit** uniquement (voir `INSTALL_PYTHON27.md`)

### Erreur "Already recording"

**Cause:** Enregistrement audio précédent non arrêté

**Solution:** Le script gère maintenant automatiquement l'arrêt des enregistrements précédents

### Module naoqi non trouvé

**Solution:** Le SDK est inclus dans `lib/`. Assurez-vous que:
1. Le dossier `lib/` contient les fichiers NAOqi
2. Le script ajoute `lib/` au PYTHONPATH (déjà fait)

### Erreur setAngles

**Cause:** Mauvais nombre de paramètres pour `setAngles()`

**Format correct:**
```python
motion.setAngles(joint_name, angle_value, speed_fraction)
# Exemple: motion.setAngles("RHand", 0.5, 0.8)
```

### API Groq ne répond pas

1. Vérifiez votre clé API dans `.env`
2. Vérifiez votre connexion Internet
3. Vérifiez les quotas de votre compte Groq

## 🎥 Fonctionnalités en Détail

### Animation de Réflexion
Lorsque NAO "réfléchit" après avoir écouté:
- Dit "Heummmmmmmmmmmm" pendant l'animation
- Lève le bras droit vers la tête
- Incline la tête sur le côté
- Gratte la tête avec mouvements des doigts (5 cycles)
- Retourne en position repos précise

### Écoute Active
Pendant l'enregistrement audio:
- Hochement de tête d'avant en arrière
- Durée configurable (par défaut 5 secondes)
- Indicateur visuel de progression

### Conversation Intelligente
- Historique de conversation maintenu
- Réponses contextuelles du LLM
- Transcription précise avec Whisper
- Parole naturelle en français avec accents

## 📚 Ressources

### Documentation NAOqi
- [Documentation NAOqi 2.8](http://doc.aldebaran.com/2-8/index.html)
- [API ALTextToSpeech](http://doc.aldebaran.com/2-8/naoqi/audio/altexttospeech.html)
- [API ALMotion](http://doc.aldebaran.com/2-8/naoqi/motion/almotion.html)
- [API ALAudioRecorder](http://doc.aldebaran.com/2-8/naoqi/audio/alaudiorecorder.html)
- [API ALFaceDetection](http://doc.aldebaran.com/2-8/naoqi/vision/alfacedetection.html)

### APIs Externes
- [Groq API Documentation](https://console.groq.com/docs)
- [Whisper API](https://platform.openai.com/docs/guides/speech-to-text)

## 🤝 Contribution

Ce projet est ouvert aux améliorations. N'hésitez pas à:
- Ajouter de nouvelles animations
- Améliorer les prompts LLM
- Optimiser les temps de réponse
- Ajouter de nouvelles fonctionnalités

## 📄 Licence

Ce projet est fourni à des fins éducatives et de démonstration.

---

**Développé pour NAO V3 avec NAOqi SDK 2.8**
