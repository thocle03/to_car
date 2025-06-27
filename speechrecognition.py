#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pocketsphinx import LiveSpeech
import sounddevice as sd
import numpy as np
import subprocess

def test_micro(device_index, duration=2.0, threshold=0.01):
    fs = 16000
    print(f"🎤 Test micro ({duration}s) sur le périphérique #{device_index}… Parlez maintenant")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1,
                       dtype='float32', device=device_index)
    sd.wait()
    rms = np.sqrt(np.mean(np.square(recording)))
    if rms >= threshold:
        print(f"✅ Son détecté (RMS = {rms:.4f} ≥ {threshold})")
    else:
        print(f"❌ Aucun son détecté (RMS = {rms:.4f} < {threshold})")
    return rms

def main():
    # 1) Affiche les devices pour repérer le micro USB
    print("Liste des périphériques audio disponibles :")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
            print(f"  {idx} – {dev['name']} (in:{dev['max_input_channels']})")
    MIC_DEVICE_INDEX = int(input("\nIndex du micro à tester ► "))

    # 2) Test rapide du micro
    test_micro(MIC_DEVICE_INDEX)

    # 3) Configuration pour le keyword spotting français
    MODEL_PATH = '/usr/share/pocketsphinx/model/fr-fr-ptm-5.2'
    DICT_PATH  = '/usr/share/pocketsphinx/model/fr-fr-ptm-5.2/fr.dict'
    speech = LiveSpeech(
        hmm=MODEL_PATH,
        dict=DICT_PATH,
        keyphrase='avance',
        kws_threshold=1e-20,
        audio_device=MIC_DEVICE_INDEX,
        buffer_size=2048,
        full_utt=False
    )

    # 4) Boucle d’écoute
    print("\nEn attente de « avance »… (Ctrl+C pour quitter)")
    for phrase in speech:
        print("✅ Phrase détectée : « {} »".format(phrase))
        subprocess.run(["./1.py"])
        break

if __name__ == "__main__":
    main()

