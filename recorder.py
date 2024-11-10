import tkinter as tk
from tkinter import messagebox
import requests
import threading
import re
import os
import hashlib
import time
from pydub import AudioSegment
from tkinter import ttk
from datetime import datetime

class iHeartRadioRecorder:
    def __init__(self, root):
        self.root = root
        self.root.title("iHeartRadio Recorder")
        self.root.geometry("600x500")

        self.status_label = tk.Label(root, text="Select a station and press 'Record' to start", wraplength=350)
        self.status_label.pack(pady=20)

        self.station_tree = ttk.Treeview(root, columns=("Station Name", "Description"), show="headings")
        self.station_tree.heading("Station Name", text="Station Name")
        self.station_tree.heading("Description", text="Description")
        self.station_tree.column("Station Name", width=250, anchor="w")
        self.station_tree.column("Description", width=300, anchor="w")
        self.station_tree.pack(pady=10)

        self.record_button = tk.Button(root, text="Record", command=self.start_recording)
        self.record_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=10)

        self.timer_label = tk.Label(root, text="00:00", font=("Helvetica", 16))
        self.timer_label.pack(pady=10)

        self.cache_label = tk.Label(root, text="Cache Size: 0 KB", font=("Helvetica", 12))
        self.cache_label.pack(pady=5)

        self.current_track_label = tk.Label(root, text="Current Track: N/A", font=("Helvetica", 12))
        self.current_track_label.pack(pady=5)

        self.stations = []
        self.load_stations()

        self.downloading_aac_files = set()
        self.is_recording = False
        self.cache_dir = "ihr_cache"
        self.stop_flag = False
        self.start_time = None

        self.current_track_title = None
        self.current_track_artist = None

        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.developer_label = tk.Label(root, text="Developed by Ghosty Tongue", font=("Helvetica", 8), fg="gray")
        self.developer_label.pack(side=tk.BOTTOM, pady=10)

    def load_stations(self):
        try:
            response = requests.get("https://raw.githubusercontent.com/Ghosty-Tongue/public-api/refs/heads/main/IHR/stations.json")
            stations_data = response.json()

            for station in stations_data:
                self.stations.append(station)
                self.station_tree.insert("", "end", values=(station['name'], station['description']))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load stations: {str(e)}")

    def start_recording(self):
        self.clear_previous_recording()

        selected_item = self.station_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection", "Please select a station first.")
            return

        selected_station = self.stations[self.station_tree.index(selected_item[0])]
        station_name = selected_station['name']

        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Recording {station_name}...")

        self.downloading_aac_files = set()
        self.is_recording = True
        self.stop_flag = False

        self.start_time = time.time()
        self.timer_thread = threading.Thread(target=self.update_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

        threading.Thread(target=self.record_audio, args=(selected_station,)).start()

    def stop_recording(self):
        self.is_recording = False
        self.stop_flag = True
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        print("Recording stopped.")

        threading.Thread(target=self.combine_audio_files).start()

    def update_timer(self):
        while self.is_recording:
            elapsed_time = time.time() - self.start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"{minutes:02d}:{seconds:02d}"
            self.timer_label.config(text=time_str)
            self.update_cache_info()
            time.sleep(1)

    def update_cache_info(self):
        cache_size = self.get_folder_size(self.cache_dir)
        self.cache_label.config(text=f"Cache Size: {cache_size / 1024:.2f} KB")

    def get_folder_size(self, folder_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size

    def record_audio(self, selected_station):
        try:
            m3u8_url = f"https://n3ab-e2.revma.ihrhls.com/zc{selected_station['id']}/hls.m3u8?zip=&rj-ttl=5&streamid={selected_station['id']}&pname=live_profile&companionAds=false&dist=iheart&terminalId=159&deviceName=web-mobile&rj-tok=AAABkw0KFxQAuzoCaJGbh-Xaaw&aw_0_1st.playerid=iHeartRadioWebPlayer&listenerId=&clientType=web&profileId=9434678024&aw_0_1st.skey=9434678024&host=webapp.US&playedFrom=157&stationid={selected_station['id']}&territory=US"
            response = requests.get(m3u8_url)
            m3u8_text = response.text

            match = re.search(r'#EXT-X-STREAM-INF.*\n(https://.*\.m3u8)', m3u8_text)
            if not match:
                raise Exception("Could not find the stream URL.")
            stream_url = match.group(1)

            self.process_stream(stream_url)

            while self.is_recording and not self.stop_flag:
                time.sleep(0.9)
                response = requests.get(m3u8_url)
                m3u8_text = response.text
                match = re.search(r'#EXT-X-STREAM-INF.*\n(https://.*\.m3u8)', m3u8_text)
                if match:
                    stream_url = match.group(1)
                    self.process_stream(stream_url)
                else:
                    raise Exception("Could not find the stream URL in the first m3u8.")

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            self.record_button.config(state=tk.NORMAL)

    def process_stream(self, stream_url):
        try:
            response = requests.get(stream_url)
            stream_m3u8 = response.text

            extinf_lines = re.findall(r'#EXTINF:\d+,\s*title="([^"]+)",artist="([^"]+)",', stream_m3u8)

            if not extinf_lines:
                raise Exception("No AAC files found in the stream data.")

            for i, (title, artist) in enumerate(extinf_lines):
                if i == len(extinf_lines) - 1:
                    self.current_track_title = title.strip()
                    self.current_track_artist = artist.strip()
                    self.current_track_label.config(text=f"Current Track: {self.current_track_title} - {self.current_track_artist}")
                
                if self.is_recording and not self.stop_flag:
                    audio_url = re.search(r'(https://.*\.aac)', stream_m3u8).group(1)
                    self.download_aac_file(audio_url)

        except Exception as e:
            self.status_label.config(text=f"Failed to process stream: {str(e)}")

    def download_aac_file(self, audio_url):
        retries = 7
        for attempt in range(retries):
            try:
                response = requests.get(audio_url, stream=True, timeout=10)  
                if response.status_code == 200:
                    file_name = os.path.basename(audio_url)
                    file_path = os.path.join(self.cache_dir, file_name)

                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)

                    self.downloading_aac_files.add(file_path)
                    print(f"Downloaded: {file_name}")
                    return  

                else:
                    raise Exception(f"Failed to download file, status code: {response.status_code}")

            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                    time.sleep(0.2)  
                else:
                    self.status_label.config(text=f"Failed to download file after {retries} attempts: {str(e)}")
                    print(f"Failed to download file after {retries} attempts: {str(e)}")
                    return  

    def combine_audio_files(self):
        try:
            valid_files = [
                f for f in self.downloading_aac_files if os.path.exists(f) and f.endswith(".aac")
            ]

            if valid_files:
                audio = AudioSegment.from_file(valid_files[0], format="aac")
                for file in valid_files[1:]:
                    audio += AudioSegment.from_file(file, format="aac")

                output_file = os.path.join(self.cache_dir, f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
                audio.export(output_file, format="mp3")
                print(f"Recording combined into: {output_file}")

                self.status_label.config(text="Recording complete.")
                self.clear_previous_recording()

            else:
                self.status_label.config(text="No valid audio files to combine.")
        except Exception as e:
            self.status_label.config(text=f"Failed to combine audio files: {str(e)}")

    def clear_previous_recording(self):
        for file in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, file)
            if file.endswith(".aac"):
                os.remove(file_path)
        self.downloading_aac_files.clear()

root = tk.Tk()
app = iHeartRadioRecorder(root)
root.mainloop()
