from classes.AccessPoint import *
from classes.Station import *
from classes import FrameType, StationStatus, AccessPointStatus
from time import sleep

class Simulator():
    def __init__(
                self,
                access_point,
                stations
            ):
        station_ids = [idx for idx in range(len(stations))]
        access_point.set_station_ids(station_ids)

        self.access_point = access_point
        self.stations = stations
        self.station_ids = station_ids
        self.reset()

    def iterate(self, verbose=False):
        ap_frame = self.access_point.next()

        if(ap_frame):
            ap_frame_type, station_id = ap_frame
            if (ap_frame_type == FrameType.cts):
                frame_length = self.stations[station_id].send_data()
                self.access_point.receive_frame(
                    f_type = FrameType.data,
                    f_len = frame_length,
                    station_id = station_id
                )
            if (ap_frame_type == FrameType.ack):
                self.stations[station_id].receive_ack()

        toggle_backoff = False
        for station_id in self.station_ids:
            station = self.stations[station_id]
            station.next()

            should_backoff = (
                station.status == StationStatus.waiting and 
                self.access_point.status == AccessPointStatus.idle
            )
            if (should_backoff):
                station.toggle_backoff()
                toggle_backoff = True
            elif (station.status == StationStatus.rts):
                self.access_point.receive_frame(
                    f_type = FrameType.rts,
                    station_id = station_id
                )
            elif (station.status == StationStatus.backoff):
                if (self.access_point.status == AccessPointStatus.backoff):
                    station.update_backoff()
                elif (self.access_point.status == AccessPointStatus.idle):
                    station.update_backoff()
                    toggle_backoff = True

        if (toggle_backoff):
            self.access_point.toggle_backoff()
        
        if (verbose):
            print(f'AP status: {self.access_point.status}')
            print(f'AP frame: {ap_frame}')
            for station_id in self.station_ids:
                station = self.stations[station_id]
                status = station.get_status()
                data_queue = [k for k in station.data_queue]
                print(f'{"-" * 18}STATION {station_id} {"-" * 18}')
                print(f'status: {status}\tqueue: {data_queue}')
                print(f'backoff: {station.backoff_counter} / {station.backoff_counter_max}')
            sleep(5)

    def reset(self):
        self.backoff_counter = 0
        self.access_point.reset()
        for station_id in self.station_ids:
            station = self.stations[station_id]
            station.reset()
            station.set_backoff(station_id)

    def simulate(self, N, verbose=False):
        for i in range(N):
            if (verbose):
                print('/' * 50)
                print(f'RUN: {i + 1}')
            self.iterate(verbose=verbose)

if (__name__ == '__main__'):
    ap = AccessPoint()
    st = [
        Station(
            data_period = 1,
            data_mean_time = 2,
        ),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station(),
        Station()
    ]
    sim = Simulator(ap, st)
    sim.simulate(
        N=40,
        verbose=True
    )
