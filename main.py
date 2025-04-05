import asyncio
from aioesphomeapi import APIClient, SensorState
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import threading
import numpy as np
from scipy.signal import find_peaks

# Device data
ESP32_HOST = "192.168.1.204"
ESP32_PORT = 6053
ESP32_PASSWORD = ""

# Data storage for plotting
max_data_points = 500  # Store the last 10000 data points
timestamps = deque(maxlen=max_data_points)
moisture_values = deque(maxlen=max_data_points)

# Initialize plot
fig, ax = plt.subplots()
ax.set_title("Soil Moisture Sensor Data")
ax.set_xlabel("Time")
ax.set_ylabel("Moisture (%)")
(line,) = ax.plot([], [], "b-", label="Soil Moisture (%)")
ax.legend()

# Function to update the graph dynamically
def update_graph(frame):
    line.set_data(list(timestamps), list(moisture_values))
    ax.relim()
    ax.autoscale_view()
    return line,

# Callback function to handle sensor updates
def on_sensor_update(state: SensorState):
    timestamps.append(len(timestamps))
    moisture_values.append(float(state.state))
    print(f"Moisture: {state.state}%")

async def esphome_client():
    while True:
        client = APIClient(ESP32_HOST, ESP32_PORT, ESP32_PASSWORD)
        try:
            await client.connect(login=True)
            print("Connected to ESPHome device!")

            # List all sensors
            entities = await client.list_entities_services()
            for entity in entities:
                print(f"Found entity: {entity}")

            # Subscribe to state updates
            client.subscribe_states(on_sensor_update)

            # Keep running until disconnected
            while client._connected:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Connection error: {e}")
            print("Reconnecting in 1 seconds...")
            await asyncio.sleep(5)
        finally:
            await client.disconnect()

def run_asyncio_loop():
    """ Runs asyncio loop in a separate thread """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(esphome_client())

# Start ESPHome client in a separate thread
thread = threading.Thread(target=run_asyncio_loop, daemon=True)
thread.start()

# Start Matplotlib animation in the main thread
ani = animation.FuncAnimation(fig, update_graph, interval=1000, cache_frame_data=False)
plt.show()  # Blocking, but asyncio keeps running in background thread

# Convert deque to numpy array for processing
moisture_array = np.array(list(moisture_values))

# Find peaks using prominence (relative peak detection)
peaks, properties = find_peaks(moisture_array, prominence=1, distance=30)  # Adjust prominence as needed

# Calculate intervals between peaks
if len(peaks) > 1:
    intervals = np.diff(peaks)  # Time steps between consecutive peaks
    avg_interval = np.median(intervals)
    print(f"Detected {len(peaks)} peaks.")
    print(f"Average number of samples between peaks: {avg_interval:.2f}")
    print(f"Average period time: {avg_interval*0.2:.2f} s")
else:
    print("Not enough peaks detected to calculate an average interval.")