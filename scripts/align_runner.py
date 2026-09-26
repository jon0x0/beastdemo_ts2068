"""Losslessly shift the runner three screen pixels left; keep scenery unchanged."""
def align_runner(art):
    if art.get('runner_alignment')=={'source_shift':5,'screen_x':104}:return art
    for sprite in art['sprites']:
        assert len(sprite['pixels'][0])==32
        assert all(all(row[27:]) for row in sprite['mask'])
        sprite['pixels']=[[0]*5+row[:27] for row in sprite['pixels']]
        sprite['mask']=[[1]*5+row[:27] for row in sprite['mask']]
    art['runner_alignment']={'source_shift':5,'screen_x':104}
    return art
