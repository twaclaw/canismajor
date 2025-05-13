from gtts import gTTS
from tqdm import tqdm

from stellarium import constellations

if __name__ == "__main__":
    for term in tqdm(constellations):
        tts = gTTS(term, lang="la")
        tts.save(f"{term}.mp3")
