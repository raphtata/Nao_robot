# Conversation Vocale NAO avec Groq LLM

## 📋 Description

Ce script permet à NAO d'avoir des conversations vocales intelligentes en utilisant:
- **Microphone de NAO** (ALSpeechRecognition) pour écouter
- **Groq LLM** (llama-3.3-70b-versatile) pour générer des réponses intelligentes
- **Synthèse vocale de NAO** (ALTextToSpeech) pour répondre

## 🎯 Fonctionnalités

- ✅ Reconnaissance vocale via le microphone de NAO
- ✅ Envoi des questions à Groq LLM
- ✅ Génération de réponses contextuelles et naturelles
- ✅ Historique de conversation (RAG-like)
- ✅ Réponses vocales de NAO
- ✅ Configuration via fichier .env

## 📦 Installation

### 1. Configuration de l'environnement

Le fichier `.env` contient vos identifiants Groq:

```env
GROQ_API_KEY=..
LLM_MODEL=llama-3.3-70b-versatile
```

### 2. Installation des dépendances

```bash
C:\Python27\python.exe -m pip install groq==0.4.2 python-dotenv==1.0.0 requests==2.31.0
```

Ou utilisez le script automatique (voir ci-dessous).

## 🚀 Utilisation

### Méthode 1: Script batch automatique (Recommandé)

```bash
.\run_voice_conversation.bat
```

Ce script va:
1. Vérifier Python 2.7 32-bit
2. Installer les dépendances automatiquement
3. Lancer la conversation vocale

### Méthode 2: Commande manuelle

```bash
C:\Python27\python.exe nao_voice_conversation.py
```

## 🎮 Déroulement de la conversation

1. **Initialisation**:
   - Connexion au robot NAO
   - Connexion à l'API Groq
   - Configuration de la reconnaissance vocale
   - Message de bienvenue: "Bonjour! Je suis pret a discuter avec vous."

2. **Boucle de conversation** (5 échanges par défaut):
   - NAO écoute pendant 5 secondes
   - Reconnaissance vocale du texte
   - Envoi à Groq LLM avec l'historique
   - Réception de la réponse
   - NAO prononce la réponse

3. **Fin**:
   - Message de clôture: "Merci pour cette conversation! A bientot!"

## ⚙️ Configuration

### Changer le nombre d'échanges

Dans `nao_voice_conversation.py`, ligne 277:

```python
conversation.conversation_loop(num_exchanges=5)  # Modifier le nombre ici
```

### Changer le modèle LLM

Dans le fichier `.env`:

```env
LLM_MODEL=llama-3.3-70b-versatile
```

Modèles Groq disponibles:
- `llama-3.3-70b-versatile` (recommandé)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

### Ajuster la durée d'écoute

Dans `nao_voice_conversation.py`, ligne 277:

```python
user_input = self.listen(duration=5)  # Durée en secondes
```

### Modifier le prompt système

Ligne 168-172:

```python
system_message = {
    "role": "system",
    "content": "Tu es NAO, un robot assistant sympathique et serviable. "
              "Reponds de maniere concise et naturelle en francais. "
              "Garde tes reponses courtes (2-3 phrases maximum) car elles seront "
              "prononcees par un robot."
}
```

## 🔧 Architecture technique

### Flux de données

```
Utilisateur parle
    ↓
Microphone NAO (ALSpeechRecognition)
    ↓
Texte reconnu
    ↓
Groq LLM API (avec historique)
    ↓
Réponse générée
    ↓
NAO parle (ALTextToSpeech)
```

### Modules NAOqi utilisés

- **ALSpeechRecognition**: Reconnaissance vocale
- **ALTextToSpeech**: Synthèse vocale
- **ALMemory**: Stockage des données de reconnaissance
- **ALAudioDevice**: Gestion audio

### API Groq

- **Endpoint**: Chat Completions
- **Modèle**: llama-3.3-70b-versatile
- **Température**: 0.7 (créativité modérée)
- **Max tokens**: 150 (réponses courtes)

## 📊 Historique de conversation

Le système maintient un historique des échanges pour un contexte conversationnel:

```python
self.conversation_history = [
    {"role": "user", "content": "Bonjour"},
    {"role": "assistant", "content": "Bonjour! Comment puis-je vous aider?"},
    {"role": "user", "content": "Quel temps fait-il?"},
    ...
]
```

Cet historique est envoyé à chaque requête pour que le LLM comprenne le contexte.

## ⚠️ Limitations

### Reconnaissance vocale NAO V3

- **Vocabulaire limité**: NAO V3 a des limitations sur la reconnaissance vocale
- **Environnement bruyant**: Fonctionne mieux dans un environnement calme
- **Langue**: Configuré pour le français
- **Confiance**: Seuil de confiance à 0.3 (ajustable)

### Solutions alternatives

Si la reconnaissance vocale de NAO est trop limitée, vous pouvez:

1. **Utiliser un microphone PC** avec une bibliothèque comme `speech_recognition`
2. **Utiliser Whisper API** de Groq pour la transcription audio
3. **Enregistrer l'audio** et l'envoyer à un service de transcription

## 🎨 Personnalisation avancée

### Ajouter des gestes pendant la conversation

```python
# Dans conversation_loop(), après speak()
if "bonjour" in response.lower():
    import thread
    thread.start_new_thread(wave_left_arm, (motion,))
```

### Changer la voix de NAO

```python
# Avant de démarrer la conversation
conversation.tts.setParameter("speed", 90)  # Vitesse (80-100)
conversation.tts.setParameter("pitchShift", 1.1)  # Tonalité
```

### Ajouter une mémoire persistante

```python
# Sauvegarder l'historique dans un fichier
import json

def save_history(self):
    with open('conversation_history.json', 'w') as f:
        json.dump(self.conversation_history, f)

def load_history(self):
    try:
        with open('conversation_history.json', 'r') as f:
            self.conversation_history = json.load(f)
    except:
        self.conversation_history = []
```

## 🐛 Dépannage

### Erreur: "GROQ_API_KEY non trouve"

- Vérifiez que le fichier `.env` existe dans le dossier du projet
- Vérifiez que la clé API est correcte

### Erreur: "Aucun texte reconnu"

- Parlez plus fort et plus clairement
- Rapprochez-vous du robot
- Vérifiez que le microphone de NAO fonctionne
- Augmentez la durée d'écoute

### Erreur de connexion Groq

- Vérifiez votre connexion internet
- Vérifiez que la clé API est valide
- Vérifiez les quotas de votre compte Groq

### Le robot ne répond pas

- Vérifiez la connexion réseau avec NAO
- Vérifiez que le volume est correct: `tts.setVolume(0.8)`
- Vérifiez les logs pour les erreurs

## 📝 Fichiers

- `nao_voice_conversation.py` - Script principal
- `run_voice_conversation.bat` - Lanceur automatique
- `.env` - Configuration Groq API
- `requirements.txt` - Dépendances Python
- `VOICE_CONVERSATION.md` - Cette documentation

## 🔗 Ressources

- [Groq API Documentation](https://console.groq.com/docs)
- [ALSpeechRecognition](http://doc.aldebaran.com/2-5/naoqi/audio/alspeechrecognition.html)
- [ALTextToSpeech](http://doc.aldebaran.com/2-5/naoqi/audio/altexttospeech.html)
- [Llama 3.3 Model Card](https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct)

## 💡 Idées d'amélioration

- [ ] Utiliser Whisper API pour une meilleure transcription
- [ ] Ajouter la détection d'intention pour déclencher des actions
- [ ] Intégrer avec le suivi facial pour une interaction plus naturelle
- [ ] Ajouter des gestes contextuels basés sur la réponse
- [ ] Sauvegarder les conversations dans une base de données
- [ ] Ajouter un système de RAG avec des documents externes
- [ ] Implémenter la détection d'émotion dans la voix
- [ ] Ajouter un mode "streaming" pour des réponses plus rapides

## 🎯 Exemple d'utilisation

```python
# Créer une conversation personnalisée
conversation = VoiceConversation("169.254.201.219")
conversation.connect()
conversation.initialize_groq()
conversation.configure_speech_recognition()

# Personnaliser le prompt
conversation.conversation_history.append({
    "role": "system",
    "content": "Tu es un expert en robotique qui adore parler de technologie."
})

# Lancer la conversation
conversation.conversation_loop(num_exchanges=10)
```

Cette fonctionnalité transforme NAO en un véritable assistant conversationnel intelligent! 🤖💬
