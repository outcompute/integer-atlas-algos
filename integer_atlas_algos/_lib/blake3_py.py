"""Pure-Python BLAKE3 (hash mode), following the official reference design.

This is the dependency-free fallback used when the fast `blake3` package is not
installed, so a shard's blake3 hash is always populated. It is correct but slow;
the executor prefers the native library when available. Validated against the
official BLAKE3 test vectors (see tests/test_blake3.py).
"""

IV = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
      0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19]

MSG_PERMUTATION = [2, 6, 3, 10, 7, 0, 4, 13, 1, 11, 12, 5, 9, 14, 15, 8]

CHUNK_START = 1 << 0
CHUNK_END = 1 << 1
PARENT = 1 << 2
ROOT = 1 << 3

BLOCK_LEN = 64
CHUNK_LEN = 1024
MASK = 0xFFFFFFFF


def _rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def _g(s, a, b, c, d, mx, my):
    s[a] = (s[a] + s[b] + mx) & MASK
    s[d] = _rotr(s[d] ^ s[a], 16)
    s[c] = (s[c] + s[d]) & MASK
    s[b] = _rotr(s[b] ^ s[c], 12)
    s[a] = (s[a] + s[b] + my) & MASK
    s[d] = _rotr(s[d] ^ s[a], 8)
    s[c] = (s[c] + s[d]) & MASK
    s[b] = _rotr(s[b] ^ s[c], 7)


def _round(s, m):
    _g(s, 0, 4, 8, 12, m[0], m[1])
    _g(s, 1, 5, 9, 13, m[2], m[3])
    _g(s, 2, 6, 10, 14, m[4], m[5])
    _g(s, 3, 7, 11, 15, m[6], m[7])
    _g(s, 0, 5, 10, 15, m[8], m[9])
    _g(s, 1, 6, 11, 12, m[10], m[11])
    _g(s, 2, 7, 8, 13, m[12], m[13])
    _g(s, 3, 4, 9, 14, m[14], m[15])


def _compress(cv, block_words, counter, block_len, flags):
    s = [
        cv[0], cv[1], cv[2], cv[3], cv[4], cv[5], cv[6], cv[7],
        IV[0], IV[1], IV[2], IV[3],
        counter & MASK, (counter >> 32) & MASK, block_len, flags,
    ]
    m = list(block_words)
    for r in range(7):
        _round(s, m)
        if r < 6:
            m = [m[MSG_PERMUTATION[i]] for i in range(16)]
    for i in range(8):
        s[i] ^= s[i + 8]
        s[i + 8] ^= cv[i]
    return s


def _words(block64):
    return [int.from_bytes(block64[i:i + 4], "little") for i in range(0, 64, 4)]


class _Output:
    __slots__ = ("cv", "block_words", "counter", "block_len", "flags")

    def __init__(self, cv, block_words, counter, block_len, flags):
        self.cv = cv
        self.block_words = block_words
        self.counter = counter
        self.block_len = block_len
        self.flags = flags

    def chaining_value(self):
        return _compress(self.cv, self.block_words, self.counter,
                         self.block_len, self.flags)[:8]

    def root_bytes(self, length):
        out = bytearray()
        counter = 0
        while length > 0:
            words = _compress(self.cv, self.block_words, counter,
                              self.block_len, self.flags | ROOT)
            block = b"".join(w.to_bytes(4, "little") for w in words)
            take = min(len(block), length)
            out += block[:take]
            length -= take
            counter += 1
        return bytes(out)


class _ChunkState:
    def __init__(self, counter):
        self.cv = list(IV)
        self.counter = counter
        self.block = bytearray(BLOCK_LEN)
        self.block_len = 0
        self.blocks_compressed = 0

    def length(self):
        return BLOCK_LEN * self.blocks_compressed + self.block_len

    def _start_flag(self):
        return CHUNK_START if self.blocks_compressed == 0 else 0

    def update(self, mv):
        pos, n = 0, len(mv)
        while pos < n:
            if self.block_len == BLOCK_LEN:
                self.cv = _compress(self.cv, _words(self.block), self.counter,
                                    BLOCK_LEN, self._start_flag())[:8]
                self.blocks_compressed += 1
                self.block_len = 0
            take = min(BLOCK_LEN - self.block_len, n - pos)
            self.block[self.block_len:self.block_len + take] = mv[pos:pos + take]
            self.block_len += take
            pos += take

    def output(self):
        padded = bytes(self.block[:self.block_len]) + b"\x00" * (BLOCK_LEN - self.block_len)
        flags = self._start_flag() | CHUNK_END
        return _Output(self.cv, _words(padded), self.counter, self.block_len, flags)


def _parent_output(left_cv, right_cv):
    return _Output(list(IV), left_cv + right_cv, 0, BLOCK_LEN, PARENT)


class Blake3:
    def __init__(self):
        self._chunk = _ChunkState(0)
        self._stack = []

    def _add_chunk_cv(self, new_cv, total_chunks):
        while total_chunks & 1 == 0:
            new_cv = _parent_output(self._stack.pop(), new_cv).chaining_value()
            total_chunks >>= 1
        self._stack.append(new_cv)

    def update(self, data):
        mv = memoryview(data)
        pos, n = 0, len(mv)
        while pos < n:
            if self._chunk.length() == CHUNK_LEN:
                cv = self._chunk.output().chaining_value()
                total = self._chunk.counter + 1
                self._add_chunk_cv(cv, total)
                self._chunk = _ChunkState(total)
            take = min(CHUNK_LEN - self._chunk.length(), n - pos)
            self._chunk.update(mv[pos:pos + take])
            pos += take
        return self

    def digest(self, length=32):
        output = self._chunk.output()
        for cv in reversed(self._stack):
            output = _parent_output(cv, output.chaining_value())
        return output.root_bytes(length)

    def hexdigest(self, length=32):
        return self.digest(length).hex()


def blake3_hexdigest(data, length=32):
    return Blake3().update(data).hexdigest(length)
