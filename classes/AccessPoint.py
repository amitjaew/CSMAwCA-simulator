from random import randint
from collections import deque
from . import FrameType, AccessPointStatus

class AccessPoint:
    station_ids = []
    target_station = -1

    status: AccessPointStatus = AccessPointStatus.idle
    status_queue = deque()
    state_counter = 0
    state_counter_max = 0    

    T_rts = 1
    T_cts = 1
    T_ack = 1
    T_sifs = 1
    T_difs = 3
    CW_min = 7
    CW_max = 1023
    CW = CW_min

    def __init__(
                self,
                T_rts = 1,
                T_cts = 1,
                T_ack = 1,
                T_sifs = 1,
                T_difs = 3,
                CW_min = 7,
                CW_max = 1023
            ):
        self.T_rts = T_rts
        self.T_cts = T_cts + T_sifs
        self.T_ack = T_ack + T_difs
        self.T_sifs = T_sifs
        self.T_difs = T_difs
        self.CW_min = CW_min
        self.CW_max = CW_max

    ##########################################
    #       GLOBAL STATE HANDLING API        #
    ##########################################
    def reset(self):
        self.status = AccessPointStatus.idle
        self.status_queue = deque()
        self.state_counter = 0
        self.state_counter_max = 0

    def set_station_ids(self, station_ids):
        self.station_ids = station_ids

    def toggle_backoff(self):
        self.status = AccessPointStatus.backoff

    def get_backoff(self):
        return randint(1, self.CW)

    def receive_frame(
                self,
                f_type: FrameType,
                station_id: int,
                f_len: int=None
            ):
        should_pass = (
            self.status != AccessPointStatus.idle and
            self.status != AccessPointStatus.backoff
        )
        if (should_pass):
            return False
        
        expecting_data = (
            self.target_station == station_id and
            f_type == FrameType.data
        )
        if (expecting_data):
            # Dataframe Receiving State
            self.status = AccessPointStatus.data
            self.set_state_counter(f_len)

            # Next States
            self.status_queue = deque([
                AccessPointStatus.sifs,
                AccessPointStatus.ack,
            ])

        elif (f_type == FrameType.rts):
            self.status = AccessPointStatus.rts
            self.target_station = station_id
            self.set_state_counter(self.T_rts)
            
            # Send CTS frame and wait SIFS
            self.status_queue = deque([
                AccessPointStatus.sifs,
                AccessPointStatus.cts,
            ])

    ##########################################
    #          LOCAL STATE HANDLING          #
    ##########################################

    def set_state_counter(self, value):
        self.state_counter_max = value
        self.state_counter = 0

    def next(self):
        should_pass = (
            self.status == AccessPointStatus.idle or
            self.status == AccessPointStatus.backoff
        )
        if (should_pass):
            return False

        if (self.state_counter == self.state_counter_max - 1):
            return self.state_handler()

        self.state_counter += 1
        return False

    def state_handler(self):
        output = False

        # Finish sending CTS frame though channel
        if (self.status == AccessPointStatus.cts):
            self.status = AccessPointStatus.idle
            self.set_state_counter(0)
            output = FrameType.cts, self.target_station

        # Finish sending ACK frame though channel
        elif (self.status == AccessPointStatus.ack):
            self.status = AccessPointStatus.idle
            self.set_state_counter(0)
            output = FrameType.ack, self.target_station
            self.target_station = -1

        elif (len(self.status_queue) > 0):
            self.status = self.status_queue.popleft()

            if (self.status == AccessPointStatus.cts):
                self.set_state_counter(self.T_cts)
            if (self.status == AccessPointStatus.ack):
                self.set_state_counter(self.T_ack)
            if (self.status == AccessPointStatus.sifs):
                self.set_state_counter(self.T_sifs)
            if (self.status == AccessPointStatus.difs):
                self.set_state_counter(self.T_difs)

        else:
            self.status = AccessPointStatus.idle
            self.set_state_counter(0)

        return output
