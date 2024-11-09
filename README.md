# iHeartRadio Recorder

A simple Python application that allows you to record live radio streams from iHeartRadio stations. The application uses the `requests` library to stream audio and the `pydub` library to combine the downloaded AAC files into a single MP3 file.

### Features

- **Select a Station**: Choose a station from a list of available iHeartRadio stations.
- **Start/Stop Recording**: Record the live audio from the selected station, and stop the recording when you're done.
- **Track Info Display**: Displays the current track's title and artist information.
- **Cache Management**: Shows the size of the audio cache and removes downloaded files after recording.
- **File Naming**: Automatically saves the recording as an MP3 file named after the station, including the date and time of recording.

### Requirements

- Python 3.x
- `requests`
- `pydub`
- `tkinter` (should be installed by default with Python)

### Installation

1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/iHeartRadio-Recorder.git
   cd iHeartRadio-Recorder
   ```

2. Install the required dependencies:
   ```bash
   pip install requests pydub
   ```

3. Download and install `ffmpeg` (required for `pydub` to handle audio formats):
   - Download ffmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html).
   - Make sure ffmpeg is in your system's PATH.

4. Run the application:
   ```bash
   python app.py
   ```

### Usage

1. Launch the application.
2. Select a station from the list of available stations.
3. Click on "Record" to start recording the station's live stream.
4. Click "Stop" to stop recording. The file will be saved in the current directory with the name `<StationName>_<YYYY-MM-DD_HH-MM-SS>.mp3`.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Credits

- Developed by [Ghosty Tongue](https://github.com/Ghosty-Tongue).
- The project uses the `requests` library for HTTP requests and `pydub` for audio manipulation.
