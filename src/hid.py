import asyncio


class QRCodeReader:
    special_chars = {
        "enter": 0x28,
        "shift": 0x02,
        "space": 0x2C,
    }

    def __init__(self, device: str, buffer_size: int):
        self.device = device
        self.buffer_size = buffer_size
        self.fd = None
        self.buffer: str = []
        self._char_map = {
            **{i: chr(ord("a") + i - 0x04) for i in range(0x04, 0x1E)},  # a-z
            **{i: chr(ord("2") + i - 0x1F) for i in range(0x1E, 0x28)},  # numbers
            self.special_chars["space"]: " ",
            self.special_chars["enter"]: "\n",
        }

    def open(self):
        self.fd = open(self.device, "rb", buffering=0)

    def decode_char(self, char: int) -> str | None:
        return self._char_map.get(char)

    async def read(self, queue: asyncio.Queue):
        if not self.fd:
            await asyncio.to_thread(self.open)

        try:
            while True:
                data = await asyncio.to_thread(self.fd.read, self.buffer_size)
                if not data or len(data) < 3:
                    await asyncio.sleep(0.1)
                    continue

                control, char_byte = data[0], data[2]
                char = self.decode_char(char_byte)

                if not char:
                    await asyncio.sleep(0.1)
                    continue

                if control == self.special_chars["shift"]:
                    self.buffer.append(char.upper())
                elif char == "\n":
                    await queue.put("".join(self.buffer))
                    self.buffer.clear()
                    await asyncio.sleep(1.0)
                else:
                    self.buffer.append(char)

                await asyncio.sleep(0.1)
        except Exception as ex:
            print(f"Error reading QR code: {ex}")
