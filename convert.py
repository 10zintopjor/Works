import pyewts
EWTSCONV = pyewts.pyewts()
def ewtstobo(ewtsstr):
    res = EWTSCONV.toUnicode(ewtsstr)
    return res