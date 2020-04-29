import psutil
import time
import os

from datetime import datetime

class MemoryCap(object):

    def run(app, memoryLimit):
        process = psutil.Process(os.getpid())
        counter = 0;
        while True:
            currentUsage = process.memory_info()[0] / 1024 / 1024
            if(currentUsage > memoryLimit):
                now = datetime.now()
                timestamp = now.strftime("%m/%d/%Y, %H:%M:%S")
                print(timestamp + ": Memory limit exeeded with current Usage of" + str(currentUsage) + "MB for the " + str(
                    counter) + " time. Will close the Application after 5 Times in a row");
                if(counter >= 5):
                    print(timestamp + ": Memory limit exeeded with current Usage of" + str(currentUsage) + "MB for the " + str(
                        counter) + " time. Closing Application");
                    os._exit(1)
                else:
                    counter = counter + 1
            elif(counter > 0):
                now = datetime.now()
                timestamp = now.strftime("%m/%d/%Y, %H:%M:%S")
                print(timestamp + ": Memory usage is normal again, resetting counter")
                counter = 0
            time.sleep(5)
