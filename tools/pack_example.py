#!/usr/bin/env python3
"""Pack the app's example STL into the website's example-ring.gqm.gz (about 1 MB instead of 7.5 MB).

    python3 tools/pack_example.py ios/GoldQuote/Resources/example-ring.stl example-ring.gqm.gz

The website shows the same piece as the app, triangle for triangle: every vertex keeps its exact float bits, so the
volume, weight and quote match the app. Format (little-endian), then gzip:
  "GQM1", u32 vertex count, u32 triangle count
  vertex bytes as 12 planes (x byte 0..3, y byte 0..3, z byte 0..3), vertices in order of first use
  3 varints per triangle: 0 = the next new vertex, k > 0 = the vertex k before the next new one
readGQM() in index.html unpacks it.
"""
import gzip
import struct
import sys
from array import array


def read_binary_stl(path):
    b = open(path, "rb").read()
    n = struct.unpack_from("<I", b, 80)[0]
    if 84 + n * 50 != len(b):
        sys.exit("expected a binary STL")
    corners = []  # (x, y, z) float bit patterns
    for i in range(n):
        o = 84 + i * 50 + 12
        for v in range(3):
            corners.append(struct.unpack_from("<3I", b, o + v * 12))
    return n, corners


def pack(n, corners):
    ids, verts, idx = {}, [], bytearray()
    for c in corners:
        v = ids.get(c)
        if v is None:
            v = ids[c] = len(verts)
            verts.append(c)
            z = 0
        else:
            z = len(verts) - v
        while z >= 128:
            idx.append((z & 127) | 128)
            z >>= 7
        idx.append(z)
    planes = bytearray()
    for k in range(3):
        for j in range(4):
            planes += bytes((c[k] >> (8 * j)) & 0xFF for c in verts)
    return b"GQM1" + struct.pack("<II", len(verts), n) + bytes(planes) + bytes(idx)


def unpack(data):
    assert data[:4] == b"GQM1"
    nv, n = struct.unpack_from("<II", data, 4)
    o = 12
    verts = [[0, 0, 0] for _ in range(nv)]
    for k in range(3):
        for j in range(4):
            for i in range(nv):
                verts[i][k] |= data[o + i] << (8 * j)
            o += nv
    out, seen = [], 0
    for _ in range(n * 3):
        z = s = 0
        while True:
            b = data[o]; o += 1
            z |= (b & 127) << s; s += 7
            if b < 128:
                break
        if z == 0:
            v = seen; seen += 1
        else:
            v = seen - z
        out.append(tuple(verts[v]))
    return out


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    n, corners = read_binary_stl(src)
    raw = pack(n, corners)
    assert unpack(raw) == corners, "round trip failed"
    gz = gzip.compress(raw, 9, mtime=0)
    open(dst, "wb").write(gz)
    print(f"{n} triangles, {len(set(corners))} vertices: {len(gz):,} bytes (round trip exact)")
