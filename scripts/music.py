"""Extract the supplied ZXAYEMUL title driver with checked relative pointers."""
from pathlib import Path
import hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
SOURCE='David Whittaker - Shadow of the Beast - Title (AY) 1 (1990).ay'
def extract():
    src=ROOT/'references/music'/SOURCE
    if not src.exists():
        src.parent.mkdir(exist_ok=True)
        src.write_bytes((ROOT/SOURCE).read_bytes())
    data=src.read_bytes()
    assert data[:8]==b'ZXAYEMUL'
    def word(o):return struct.unpack_from('>H',data,o)[0]
    def pointer(o):
        p=o+struct.unpack_from('>h',data,o)[0]
        assert 0<=p<len(data)
        return p
    def string(o):return data[o:data.index(0,o)].decode('latin1')
    song=pointer(18);record=pointer(song+2);points=pointer(record+10);table=pointer(record+12)
    blocks=[];memory=bytearray(65536)
    while word(table):
        address,length=word(table),word(table+2);offset=pointer(table+4)
        assert address+length<=65536 and offset+length<=len(data)
        memory[address:address+length]=data[offset:offset+length]
        blocks.append(dict(address=address,length=length,offset=offset));table+=6
    assert blocks==[dict(address=0xbffe,length=4645,offset=0x109)]
    assert word(points+2)==0xc0f6 and word(points+4)==0xc003
    assert memory[0xc86c:0xc873]==bytes.fromhex('44 ed 59 45 ed 79 c9')
    # BFFE/BFFF is an unused LD A,0 wrapper preceding JP init at C000.
    # Both public calls are >=C000; retain the complete original in reference RAM.
    blob=memory[0xc000:0xd223]
    meta=dict(source=SOURCE,sha256=hashlib.sha256(data).hexdigest(),author=string(pointer(12)),
              title=string(pointer(song)),song=0,songs=data[16]+1,length_ticks=word(record+4),
              init=word(points+2),play=word(points+4),load=0xc000,bytes=len(blob),
              patch_address=0xc86c,original_patch='44ed5945ed79c9',blocks=blocks)
    (ROOT/'build/music-original.bin').write_bytes(memory)
    (ROOT/'build/music.json').write_text(json.dumps(meta,indent=2)+'\n')
    return blob,meta
if __name__=='__main__':
    _,meta=extract();print(json.dumps(meta,indent=2))
