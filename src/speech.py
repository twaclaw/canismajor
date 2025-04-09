import asyncio

import sounddevice as sd
import speech_recognition as sr
from jellyfish import levenshtein_distance, metaphone

sd.default.device = "Microphone [USB Microphone]"
class SpeechMatch:
    def __init__(self, vocab: dict[str, str], language: str = "english"):
        self.vocab = vocab if language == "english" else {word: word for word in vocab}
        self.phonetic = {word: metaphone(word) for word in vocab}

    def listen(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        while True:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source)
                try:
                    command = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    print("error")
                    continue

            command = command.title()
            if command in self.vocab:
                command_english = self.vocab[command]
                asyncio.run_coroutine_threadsafe(queue.put(command_english), loop)
                continue

            phonetic = metaphone(command)

            # Non-decreasing list of distances
            monotonic: list[tuple[str, str]] = []

            for word in self.vocab:
                dist = levenshtein_distance(phonetic, self.phonetic[word])
                if dist <= 1:
                    command_english = self.vocab[word]
                    asyncio.run_coroutine_threadsafe(queue.put(command_english), loop)
                    monotonic.clear()
                    break

                while monotonic and dist < monotonic[-1][0]:
                    monotonic.pop()

                monotonic.append((dist, word))

            # If there is only one word with the smallest distance
            if len(monotonic) == 1:
                command_english = self.vocab[monotonic[0][1]]
                asyncio.run_coroutine_threadsafe(queue.put(command_english), loop)
                continue

            # All matches corresponding to the smallest phonetic distance
            possible_matches = [
                word for dist, word in monotonic if dist == monotonic[0][0]
            ]

            if len(possible_matches) == 1:
                command_english = self.vocab[possible_matches[0]]
                asyncio.run_coroutine_threadsafe(queue.put(command_english), loop)

            # TODO: check if it is required to try further matching
