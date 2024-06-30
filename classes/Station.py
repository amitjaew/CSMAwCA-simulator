from . import StationStatus, FrameType
from collections import deque
from random import expovariate
from math import ceil

MAX_CLOCK = 1000000

class Station:
    status = StationStatus.idle
    data_period = 20    #V.A
    data_mean_time = 5   #V.A

    data_queue = deque()
    data_queue_max = 10

    data_events = deque()
    event_memory_window = 20

    backoff_counter = 0
    backoff_counter_max = 0
    canceled_counter = 0
    success_counter = 0

    time_counter = 0

    def __init__(
                self,
                data_period = 200,
                data_mean_time = 5,
                data_queue_max = 10,
                event_memory_window = 20,
            ):
        self.data_period = data_period
        self.data_mean_time = data_mean_time
        self.data_queue_max = data_queue_max
        self.event_memory_window = event_memory_window
    
    ##########################################
    #       GLOBAL STATE HANDLING API        #
    ##########################################
    def reset(self):
        self.status = StationStatus.idle
        self.data_queue = deque()
        self.data_events = deque()
        self.backoff_counter = 0
        self.backoff_counter_max = 0
        self.canceled_counter = 0
        self.success_counter = 0
        self.time_counter = 0

    def send_data(self):
        self.success_counter += 1
        self.status = StationStatus.data
        return self.data_queue.popleft()

    def rts_sended(self):
        self.status = StationStatus.rts

    def receive_ack(self):
        self.status = StationStatus.idle

    def toggle_backoff(self):
        if (self.status != StationStatus.waiting):
            return
        self.status = StationStatus.backoff
        self.backoff_counter = 0
    
    def set_backoff(self, value):
        self.backoff_counter_max = value

    def update_backoff(self):
        self.backoff_counter += 1

    ##########################################
    #          LOCAL STATE HANDLING          #
    ##########################################

    def has_data_pending(self):
        return len(self.data_queue) > 0
    
    # Update data_queue with poisson random variable
    def queue_incoming_event(self):
        event_time = 0
        if len(self.data_queue) == 0:
            event_time = expovariate(1/self.data_period)
        else:
            event_time = expovariate(1/self.data_period) + self.data_events[-1]
        
        self.data_events.append(event_time % MAX_CLOCK)

    def is_data_outgoing(self):
        if (self.status == StationStatus.data):
            return False

        return ceil(self.data_events[0]) == self.time_counter

    # Manage Station as a finite state machine with random variables
    def next(self):
        # Keep event window length constant
        while (len(self.data_events) < self.event_memory_window):
            self.queue_incoming_event()

        # Checks for outgoing data events
        while (self.is_data_outgoing()):

            self.data_events.popleft()
            self.data_queue.append(
                    ceil(expovariate(1/self.data_mean_time))
                )
            # Drops dataframes that exceed data queue length
            while (len(self.data_queue) > self.data_queue_max):
                self.data_queue.pop()
                self.canceled_counter += 1

        if (self.status == StationStatus.idle and self.has_data_pending()):
            self.status = StationStatus.waiting

        self.time_counter = (self.time_counter + 1) % MAX_CLOCK

    def get_status(self):
        return self.status
