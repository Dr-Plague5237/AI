# vosk_to_ollama.py
import json
import requests
import sounddevice as sd
import scipy.io.wavfile as wavfile
from vosk import Model, KaldiRecognizer

# Adjust these
RATE = 16000
DURATION = 5          # seconds to record
VOSK_MODEL_PATH = "/home/bathrinath/ICAARS/edgeAI/models/vosk-model-en-us-0.22"  # change to your model folder
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"   # change to the model you have pulled

def record_wav(filename="input.wav", duration=DURATION, fs=RATE):
    print(f"Recording {duration}s...")
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    wavfile.write(filename, fs, rec)
    print(f"Saved {filename}")
    return filename

def transcribe_wav(vosk_model_path, wav_path):
    model = Model(vosk_model_path)
    wf_rate, data = wavfile.read(wav_path)
    if wf_rate != RATE:
        raise RuntimeError(f"Expected sample rate {RATE}, got {wf_rate}")
    rec = KaldiRecognizer(model, RATE)
    rec.SetWords(True)
    # feed in data in chunks
    import math
    step = 4000
    offset = 0
    text = ""
    while offset < len(data):
        chunk = data[offset:offset+step].tobytes()
        if rec.AcceptWaveform(chunk):
            res = json.loads(rec.Result())
            text += (res.get("text","") + " ")
        offset += step
    final = json.loads(rec.FinalResult())
    text += final.get("text","")
    return text.strip()

def query_ollama(prompt_text):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    wav = record_wav()
    transcript = transcribe_wav(VOSK_MODEL_PATH, wav)
    print("TRANSCRIPT:", transcript)
    if not transcript:
        print("No speech detected.")
        raise SystemExit(1)

    # Optional: build a system prompt or instruction around the transcript
    full_prompt = f"You are an assistant. The user said: '{transcript}'. Produce a concise plan for generating a CAD part."

    response = query_ollama(full_prompt)
    # Ollama's non-stream response usually has 'response' or 'choices' depending on model/API mode
    print("OLLAMA RAW RESPONSE:")
    print(json.dumps(response, indent=2))
    # try to extract the visible text
    if "response" in response:
        print("\nOUTPUT:\n", response["response"])
    elif "choices" in response:
        print("\nOUTPUT:\n", response["choices"][0].get("message", {}).get("content", ""))
    else:
        print("\nFull response object shown above.")
