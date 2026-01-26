# Suivi Facial avec Caméra Embarquée NAO

## 📋 Description

Ce script utilise **directement la caméra embarquée de NAO** et les modules internes du SDK NAOqi pour détecter et suivre les visages. Plus besoin de webcam PC!

## 🎯 Avantages par rapport à la version webcam

- ✅ **Pas de dépendances externes** (OpenCV, NumPy) - utilise uniquement le SDK NAOqi
- ✅ **Utilise la caméra de NAO** - le robot voit avec ses propres yeux
- ✅ **Module ALFaceDetection** - détection optimisée pour NAO
- ✅ **Module ALTracker** - suivi automatique et fluide
- ✅ **Plus simple** - moins de code, plus de fonctionnalités natives

## 🤖 Modules NAOqi utilisés

### 1. **ALFaceDetection**
Module de détection de visages intégré à NAO:
- Détection en temps réel via la caméra embarquée
- Optimisé pour les performances du robot
- Retourne la position et les informations des visages détectés

### 2. **ALTracker**
Module de suivi automatique:
- Contrôle automatique de la tête pour suivre une cible
- Mode "Head" - suivi avec la tête uniquement
- Suivi fluide et naturel
- Gestion automatique des limites de mouvement

### 3. **ALMemory**
Stockage des données détectées:
- Clé `FaceDetected` contient les informations des visages
- Mise à jour en temps réel

## 🚀 Utilisation

### Lancement automatique (Recommandé)

```bash
.\run_face_tracking_nao.bat
```

### Lancement manuel

```bash
C:\Python27\python.exe nao_face_tracking_nao_camera.py
```

## 📦 Installation

**Aucune dépendance externe requise!** Le script utilise uniquement le SDK NAOqi déjà installé.

## 🎮 Comportement

1. **Initialisation**:
   - Connexion aux modules NAOqi (ALFaceDetection, ALTracker, ALMotion)
   - Configuration de la détection de visages
   - Activation des moteurs de la tête
   - Message vocal: "Je vais maintenant suivre votre visage avec ma camera embarquee"

2. **Suivi actif**:
   - La caméra de NAO détecte les visages
   - Le module ALTracker suit automatiquement le visage le plus proche
   - La tête de NAO se déplace pour garder le visage centré
   - Affichage dans le terminal: "Visage detecte! Suivi en cours..."

3. **Arrêt**:
   - Appuyez sur **Ctrl+C** pour arrêter
   - La tête revient en position initiale
   - Les moteurs sont désactivés

## ⚙️ Configuration

### Période de détection

Dans `nao_face_tracking_nao_camera.py`, ligne 68:

```python
self.face_detection.setParameter("Period", 500)  # 500ms = 2 détections/seconde
```

Valeurs possibles:
- `250` = 4 détections/seconde (plus réactif, plus de CPU)
- `500` = 2 détections/seconde (équilibré)
- `1000` = 1 détection/seconde (économe)

### Mode de suivi

Ligne 91:

```python
self.tracker.setMode("Head")  # Suivi avec la tête uniquement
```

Autres modes possibles:
- `"Head"` - Tête uniquement (recommandé)
- `"WholeBody"` - Corps entier (robot peut se déplacer)
- `"Move"` - Déplacement sans rotation du corps

## 🔧 Fonctionnement technique

### Architecture

```
NAO Camera → ALVideoDevice → ALFaceDetection → ALMemory
                                                    ↓
                                              FaceDetected
                                                    ↓
                                               ALTracker → ALMotion → Head Motors
```

### Données de détection

Les données dans `ALMemory["FaceDetected"]` contiennent:
- `faces[0]` - Timestamp de la détection
- `faces[1]` - Liste des visages détectés
  - Position (x, y) dans l'image
  - Taille du visage
  - Informations supplémentaires (âge, genre si activé)

### Suivi automatique

Le module ALTracker:
1. Lit les positions des visages depuis ALMemory
2. Calcule les angles nécessaires pour centrer le visage
3. Envoie les commandes à ALMotion
4. Répète en boucle pour un suivi fluide

## 📊 Comparaison des deux méthodes

| Caractéristique | Webcam PC | Caméra NAO |
|----------------|-----------|------------|
| Dépendances | OpenCV, NumPy | Aucune |
| Installation | Complexe | Simple |
| Performance | Dépend du PC | Optimisé NAO |
| Affichage vidéo | Oui | Non |
| Simplicité | Moyenne | Élevée |
| Autonomie robot | Non | Oui |

## ⚠️ Dépannage

### Erreur: "Cannot connect to ALFaceDetection"

- Vérifiez que le robot est allumé
- Vérifiez la connexion réseau: `ping 169.254.201.219`
- Redémarrez le robot si nécessaire

### Le robot ne détecte pas les visages

- **Éclairage**: Assurez-vous d'avoir un bon éclairage
- **Distance**: Placez-vous à 1-3 mètres du robot
- **Hauteur**: Mettez-vous à hauteur de la caméra de NAO
- **Angle**: Regardez le robot de face

### Le suivi est saccadé

- Augmentez la période de détection: `setParameter("Period", 1000)`
- Vérifiez la charge CPU du robot
- Assurez-vous qu'aucun autre module n'utilise la caméra

### Erreur: "Target already registered"

Le tracker a déjà une cible enregistrée. Redémarrez le script ou appelez:
```python
tracker.unregisterAllTargets()
```

## 🎨 Personnalisation

### Suivre plusieurs visages

Actuellement, ALTracker suit le visage le plus proche. Pour changer ce comportement, modifiez la logique dans `monitor_tracking()`.

### Ajouter des réactions

Combinez avec d'autres modules:

```python
# Saluer quand un visage est détecté
if not self.face_detected and faces:
    self.tts.say("Bonjour!")
    # Appeler wave_left_arm()
```

### Utiliser la caméra du bas

Par défaut, NAO utilise la caméra du haut. Pour changer:

```python
video = ALProxy("ALVideoDevice", self.nao_ip, self.nao_port)
video.setActiveCamera(1)  # 0 = caméra du haut, 1 = caméra du bas
```

## 📝 Fichiers

- `nao_face_tracking_nao_camera.py` - Script principal (caméra NAO)
- `run_face_tracking_nao.bat` - Lanceur automatique
- `nao_face_tracking.py` - Version webcam PC (alternative)
- `FACE_TRACKING_NAO_CAMERA.md` - Cette documentation

## 🔗 Ressources

- [ALFaceDetection Documentation](http://doc.aldebaran.com/2-5/naoqi/vision/alfacedetection.html)
- [ALTracker Documentation](http://doc.aldebaran.com/2-5/naoqi/trackers/altracker.html)
- [ALVideoDevice Documentation](http://doc.aldebaran.com/2-5/naoqi/vision/alvideodevice.html)
- [NAO Camera Specifications](http://doc.aldebaran.com/2-5/family/nao_technical/video_naov6.html)

## 💡 Idées d'amélioration

- [ ] Ajouter la reconnaissance de visages connus (ALFaceCharacteristics)
- [ ] Faire parler NAO quand il reconnaît quelqu'un
- [ ] Ajouter des expressions faciales (LEDs des yeux)
- [ ] Combiner avec le geste de salut
- [ ] Enregistrer les visages détectés
- [ ] Suivre avec tout le corps (mode WholeBody)
- [ ] Ajouter la détection d'émotions

## 🎯 Exemple d'utilisation avancée

```python
# Combiner suivi facial et salut
if not self.face_detected and faces:
    self.face_detected = True
    self.tts.say("Bonjour! Je vous ai detecte!")
    # Lancer le salut dans un thread
    import thread
    thread.start_new_thread(wave_left_arm, (self.motion,))
```

## ✅ Avantages de cette méthode

1. **Autonomie complète** - NAO utilise ses propres capteurs
2. **Simplicité** - Pas de configuration de webcam PC
3. **Performance** - Optimisé pour le matériel de NAO
4. **Fiabilité** - Modules testés et validés par Softbank Robotics
5. **Intégration** - S'intègre parfaitement avec les autres fonctionnalités NAO

Cette méthode est **recommandée** pour une utilisation en production!
