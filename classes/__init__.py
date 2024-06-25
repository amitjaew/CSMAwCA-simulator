from enum import Enum

class StationStatus(Enum):
    idle = 'IDLE'
    waiting = 'WAITING'
    backoff = 'BACKOFF'
    data = 'DATA'
    rts = 'RTS'

class AccessPointStatus(Enum):
    idle = 'IDLE'
    backoff = 'BACKOFF'
    data = 'DATA'
    ack = 'ACK'
    rts = 'RTS'
    cts = 'CTS'
    sifs = 'SIFS'
    difs = 'DIFS'

class FrameType(Enum):
    ack = 'ACK'
    rts = 'RTS'
    cts = 'CTS'
    data = 'DATA'

