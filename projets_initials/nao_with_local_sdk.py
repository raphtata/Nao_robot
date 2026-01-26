#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour faire parler le robot NAO V3
Utilise Python 2.7 avec le SDK NAOqi local (dossier lib/)
Adresse IP du robot: 169.254.201.219
"""

import sys
import os
import time
import thread

# Ajouter le dossier lib local au path
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, lib_path)

print("=" * 60)
print("         CONTROLE DU ROBOT NAO V3")
print("=" * 60)
print()
print("Version Python:", sys.version)
print("SDK NAOqi depuis:", lib_path)
print()

# Importer le SDK NAOqi
try:
    from naoqi import ALProxy
    print("OK SDK NAOqi charge avec succes!")
except ImportError as e:
    print("X Erreur: Impossible de charger le SDK NAOqi")
    print("Erreur:", str(e))
    print()
    print("Verifiez que:")
    print("  - Vous utilisez Python 2.7")
    print("  - Le dossier 'lib' contient tous les fichiers du SDK")
    print("  - Les fichiers .pyd sont compatibles avec votre version de Python")
    sys.exit(1)

print()


def wave_left_arm(motion):
    """Fait saluer le robot avec le bras gauche"""
    try:
        # Verrouiller les hanches et les jambes pour stabiliser le robot
        print("Verrouillage des hanches et jambes pour stabilite...")
        motion.setStiffnesses("LLeg", 1.0)
        motion.setStiffnesses("RLeg", 1.0)
        time.sleep(0.3)
        
        # Activer les moteurs du bras
        motion.setStiffnesses("LArm", 1.0)
        
        # Positions pour le salut (en radians)
        # LShoulderPitch: lever le bras
        # LShoulderRoll: ecarter le bras du corps
        # LElbowYaw: rotation du coude
        # LElbowRoll: plier le coude
        # LWristYaw: rotation du poignet
        
        names = ["LShoulderPitch", "LShoulderRoll", "LElbowYaw", "LElbowRoll", "LWristYaw"]
        
        # Position de depart pour le coucou (bras leve sur le cote)
        # LShoulderPitch: -0.5 (bras leve a hauteur d'epaule)
        # LShoulderRoll: 0.8 (bras bien ecarte du corps)
        # LElbowYaw: -1.2 (coude vers l'exterieur)
        # LElbowRoll: -1.5 (coude plie a 90 degres)
        # LWristYaw: 0.0 (poignet droit)
        angles_up = [-0.5, 0.8, -1.2, -1.5, 0.0]
        motion.setAngles(names, angles_up, 0.3)
        time.sleep(1.5)
        
        # Mouvement de coucou (balancement de l'avant-bras)
        for _ in range(4):
            # Ouvrir l'avant-bras vers l'exterieur
            motion.setAngles("LElbowRoll", -0.5, 0.6)
            time.sleep(0.6)
            # Ramener l'avant-bras vers l'interieur
            motion.setAngles("LElbowRoll", -1.5, 0.6)
            time.sleep(0.6)
        
        # Position finale de l'avant-bras
        motion.setAngles("LElbowRoll", -1.0, 0.3)
        time.sleep(0.3)
        
        # Ramener le bras en position repos
        angles_rest = [1.5, 0.15, -1.5, -0.5, 0.0]
        motion.setAngles(names, angles_rest, 0.3)
        time.sleep(1.0)
        
        # Desactiver les moteurs du bras
        motion.setStiffnesses("LArm", 0.0)
        
        # Deverrouiller les hanches et les jambes
        print("Deverrouillage des hanches et jambes...")
        motion.setStiffnesses("LLeg", 0.0)
        motion.setStiffnesses("RLeg", 0.0)
        
    except Exception as e:
        print("Erreur lors du mouvement du bras:", str(e))


def scratch_head(motion, tts):
    """Fait gratter le crane au robot avec le bras droit"""
    try:
        # Verrouiller les hanches et les jambes pour stabiliser le robot
        print("Verrouillage des hanches et jambes pour stabilite...")
        motion.setStiffnesses("LLeg", 1.0)
        motion.setStiffnesses("RLeg", 1.0)
        time.sleep(0.3)
        
        # Activer les moteurs du bras droit et de la tete
        motion.setStiffnesses("RArm", 1.0)
        motion.setStiffnesses("Head", 1.0)
        time.sleep(0.3)
        
        # Positions pour se gratter le crane (en radians)
        # RShoulderPitch: lever le bras
        # RShoulderRoll: rapprocher le bras de la tete
        # RElbowYaw: rotation du coude
        # RElbowRoll: plier le coude
        # RWristYaw: rotation du poignet
        
        names = ["RShoulderPitch", "RShoulderRoll", "RElbowYaw", "RElbowRoll", "RWristYaw"]
        
        # Lever le bras vers la tete
        # RShoulderPitch: -1.0 (bras leve vers le haut)
        # RShoulderRoll: -0.3 (bras rapproche de la tete)
        # RElbowYaw: 1.5 (coude vers l'interieur)
        # RElbowRoll: 1.5 (coude plie)
        # RWristYaw: 0.0 (poignet droit)
        angles_up = [-1.0, -0.3, 1.5, 1.5, 0.0]
        motion.setAngles(names, angles_up, 0.3)
        time.sleep(1.5)
        
        # Incliner legerement la tete vers l'avant pour faciliter le geste
        motion.setAngles("HeadPitch", 0.3, 0.3)
        time.sleep(0.5)
        
        # Dire la phrase pendant le grattage
        import thread
        thread.start_new_thread(tts.say, ("Hmm, Beine qui refait ses veuche , Flo qui refait ses boubs mais ou va la France",))
        time.sleep(0.5)
        
        # Mouvement de grattage (petits mouvements du poignet)
        for _ in range(5):
            # Rotation du poignet pour gratter
            motion.setAngles("RWristYaw", 0.5, 0.8)
            time.sleep(0.2)
            motion.setAngles("RWristYaw", -0.5, 0.8)
            time.sleep(0.2)
        
        # Remettre le poignet au centre
        motion.setAngles("RWristYaw", 0.0, 0.3)
        time.sleep(0.3)
        
        # Remettre la tete droite
        motion.setAngles("HeadPitch", 0.0, 0.3)
        time.sleep(0.5)
        
        # Ramener le bras en position repos
        angles_rest = [1.5, -0.15, 1.5, 0.5, 0.0]
        motion.setAngles(names, angles_rest, 0.3)
        time.sleep(1.0)
        
        # Desactiver les moteurs du bras et de la tete
        motion.setStiffnesses("RArm", 0.0)
        motion.setStiffnesses("Head", 0.0)
        
        # Deverrouiller les hanches et les jambes
        print("Deverrouillage des hanches et jambes...")
        motion.setStiffnesses("LLeg", 0.0)
        motion.setStiffnesses("RLeg", 0.0)
        
    except Exception as e:
        print("Erreur lors du grattage de tete:", str(e))


def main():
    """Fonction principale"""
    NAO_IP = "169.254.201.219"
    NAO_PORT = 9559
    
    try:
        print("Connexion au robot NAO a %s:%d..." % (NAO_IP, NAO_PORT))
        tts = ALProxy("ALTextToSpeech", NAO_IP, NAO_PORT)
        motion = ALProxy("ALMotion", NAO_IP, NAO_PORT)
        print("OK Connexion etablie avec succes!")
        print()
        
        # Configuration de la langue
        print("Configuration de la langue en francais...")
        tts.setLanguage("French")
        print("OK Langue configuree")
        print()
        
        # Ajustement du volume
        print("Ajustement du volume...")
        tts.setVolume(0.8)
        print("OK Volume ajuste a 80%%")
        print()
        
        print("-" * 60)
        
        # Messages a prononcer
        # messages = [
        #     "Bonjour! Je suis RAPHA votre robot d'assistance.",
        #     "Je suis heureux de vous rencontrer !",
        #     "Que puis je faire pour vous aider ?"
        # ]
        
        messages = ["Bonjour mes petites merveilles"]

        # Faire parler le robot avec salut au premier message
        for i, message in enumerate(messages, 1):
            print("\nMessage %d/%d: '%s'" % (i, len(messages), message))
            
            # Faire le salut pour le premier message
            if i == 1:
                print("Debut du salut avec le bras gauche...")
                # Lancer le salut dans un thread separe pour parler en meme temps
                #thread.start_new_thread(wave_left_arm, (motion,))
                time.sleep(0.5)  # Petit delai pour que le bras commence a bouger
            
            # Parler (bloquant)
            tts.say(message)
            print("OK Message prononce")
            
            # Attendre que le salut se termine completement pour le premier message
            if i == 1:
                # Le mouvement dure: 1.5s (lever) + 4.8s (4 coucous) + 0.3s + 1.0s (descendre) = 7.6s
                time.sleep(2)  # Temps pour finir le salut
            elif i < len(messages):
                time.sleep(1)
        
        print()
        print("-" * 60)
        print("Demonstration du grattage de tete...")
        print("-" * 60)
        print()
        
        # Demonstration du grattage de tete
        time.sleep(1)
        scratch_head(motion, tts)
        time.sleep(2)
        
        print()
        print("-" * 60)
        print("OK Programme termine avec succes!")
        print("=" * 60)
        
    except Exception as e:
        print("X Erreur:", str(e))
        print()
        print("Verifiez que:")
        print("  - Le robot NAO est allume (yeux bleus)")
        print("  - L'adresse IP est correcte (169.254.201.219)")
        print("  - Le cable Ethernet est branche")
        print("  - Votre ordinateur est sur le meme reseau")
        sys.exit(1)


if __name__ == "__main__":
    main()
