import platform
import datetime
import os
from time import sleep
import psutil
from pytz import timezone


class TrajectorySaver:
    """Provides safe gps points saving (robot's trajectory)"""

    def __init__(self, full_path):
        self.__full_path = full_path
        self.__output_file = open(full_path, "w")
        self.__last_received_point = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.__output_file.close()

    def save_point(self, point: list, save_raw=False, flush_immediately=True):
        """
        Saves given point if it is different from previous received gps point.
        """

        if not str(point) == self.__last_received_point:
            self.__last_received_point = str(point)

            #if len(point)==3:
            #    str_point = str(point[0]) + " " + str(point[1])+ " " + point[2] + "\n" if save_raw else str(point) + "\n"
            #else :
            str_point = str(point[0]) + " " + str(point[1]) + "\n" if save_raw else str(point) + "\n"
                
            self.__output_file.write(str_point)

            if flush_immediately:
                self.__output_file.flush()


class Logger:
    """
    Writes into the file with specified name str data, flushing data on each receiving
    """

    def __init__(self, file_name, add_time=True, time_sep=" "):
        self._file = open(file_name, "a+")
        self._file_name = file_name
        self.__add_time = add_time
        self.__time_sep = time_sep

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.__exit__(exc_type, exc_val, exc_tb)

    def write_and_flush(self, s):
        if self.__add_time:
            s = get_current_time() + self.__time_sep + s
        self._file.write(s)
        self._file.flush()

    def write(self, s):
        if self.__add_time:
            s = get_current_time() + self.__time_sep + s
        self._file.write(s)
    
    def remove_end_line(self):
        self._file.seek(0, os.SEEK_END)

        pos = self._file.tell() - 1

        while pos > 0 and self._file.read(1) != "\n":
            pos -= 1
            self._file.seek(pos, os.SEEK_SET)

        if pos > 0:
            self._file.seek(pos, os.SEEK_SET)
            self._file.truncate()
        
        self._file.write("\n")
        self._file.flush()

    def close(self):
        self._file.close()


def get_current_time():
    """Returns current time as formatted string"""

    return datetime.datetime.now(timezone('Europe/Berlin')).strftime("%d-%m-%Y %H-%M-%S %f")


def create_directories(*args):
    """Creates directories, receives any args count, each arg is separate dir"""

    for path in args:
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except OSError:
                print("Creation of the directory %s failed" % path)
            else:
                print("Successfully created the directory %s " % path)
        else:
            print("Directory %s is already exists" % path)


def get_path_slash():
    return "\\" if platform.system() == "Windows" else "/"