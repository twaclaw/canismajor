import asyncio

from jellyfish import levenshtein_distance, metaphone


class SpeechMatch:
    def __init__(self, vocab: list[str]):
        self.vocab = vocab
        self.phonetic = {word: metaphone(word) for word in vocab}

    def listen(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        while True:
            command = input("Please say something: ") # TODO: replace by microphone input
            command = command.title()
            if command in self.vocab:
                asyncio.run_coroutine_threadsafe(queue.put(command), loop)
                continue

            phonetic = metaphone(command)
            monotonic: list[
                tuple[str, str]
            ] = []  # Monotonicly non-decreasing list of distances

            for word in self.vocab:
                dist = levenshtein_distance(phonetic, self.phonetic[word])
                if dist <= 1:
                    asyncio.run_coroutine_threadsafe(queue.put(word), loop)
                    monotonic.clear()
                    break

                while monotonic and dist < monotonic[-1][0]:
                    monotonic.pop()

                monotonic.append((dist, word))

            # If there is only one word with the smallest distance
            if len(monotonic) == 1:
                asyncio.run_coroutine_threadsafe(queue.put(monotonic[0][1]), loop)
                continue

            # All matches corresponding to the smallest phonetic distance
            possible_matches = [
                word for dist, word in monotonic if dist == monotonic[0][0]
            ]

            if len(possible_matches) == 1:
                asyncio.run_coroutine_threadsafe(queue.put(possible_matches[0]), loop)

            # TODO: check if it is required to try further matching
