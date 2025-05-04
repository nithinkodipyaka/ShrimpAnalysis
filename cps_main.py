import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, butter, sosfiltfilt
import os
from matplotlib.backends.backend_pdf import PdfPages

# Configuration Parameters
SAMPLE_RATE = 44100
PEAK_HEIGHT = 0.01  # Minimum amplitude for a shrimp click
PEAK_DISTANCE = int(SAMPLE_RATE / 100)  # ~10ms at 44100 Hz
MAX_CPS_DISPLAY = 25

# Step 1: Load the audio file
def load_audio(file_path):
    audio, sr = librosa.load(file_path, sr=SAMPLE_RATE)
    return audio, sr

# Step 2: Apply a bandpass filter (2000–6000 Hz)
def bandpass_filter(audio, sr, lowcut=2000, highcut=6000):
    sos = butter(10, [lowcut, highcut], btype='band', fs=sr, output='sos')
    filtered_audio = sosfiltfilt(sos, audio)
    return filtered_audio

# Step 3: Detect clicks and calculate CPS in each frame
def calculate_cps(audio, sr, frame_duration=1.0, threshold_energy=PEAK_HEIGHT, min_distance=PEAK_DISTANCE):
    frame_samples = int(frame_duration * sr)
    hop_samples = frame_samples
    num_frames = len(audio) // hop_samples
    cps = []
    frame_times = []
    for i in range(num_frames):
        start = i * hop_samples
        end = start + frame_samples
        frame = audio[start:end]
        peaks, _ = find_peaks(np.abs(frame), height=threshold_energy, distance=min_distance)
        clicks_in_frame = len(peaks)
        cps_value = clicks_in_frame / frame_duration
        cps.append(cps_value)
        frame_times.append((start + end) / (2 * sr))
    cps = np.array(cps)
    window_size = 5
    cps = np.convolve(cps, np.ones(window_size)/window_size, mode='same')
    return cps, np.array(frame_times)

# Step 4: Plot the CPS over time
def plot_aggregated_cps(time_axis, cps_values, audio_duration, max_cps=MAX_CPS_DISPLAY, file_title="Audio File"):
    cps_truncated = np.clip(cps_values, 0, max_cps)
    plt.figure(figsize=(10, 3))
    plt.plot(time_axis, cps_truncated, linestyle='-', color='blue')
    plt.axhline(max_cps, color='red', linestyle='--', linewidth=1, label=f"Max Display CPS = {max_cps}")
    plt.title(f"Aggregated CPS (Click Rate) Over Time - {file_title}")
    plt.xlabel("Time (s)")
    plt.ylabel("CPS")
    plt.ylim(0, max_cps + 1)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    return plt.gcf()

# Function to add text to PDF with exact formatting
def add_text_to_pdf(pdf, text):
    fig, ax = plt.subplots(figsize=(10, 3))  # Match graph size
    ax.axis('off')
    # Use monospace font to preserve alignment, no additional title
    ax.text(0.05, 0.95, text, fontsize=10, family='monospace', verticalalignment='top')
    pdf.savefig(fig)
    plt.close(fig)

# Main function to analyze CPS and collect results
def analyze_cps(file_path, pdf):
    audio, sr = load_audio(file_path)
    audio_duration = len(audio) / sr
    file_title = os.path.basename(file_path)
    
    # Collect text results exactly as they would be printed
    text_results = []
    text_results.append(f"\n===== Processing: {file_title} =====")
    text_results.append(f"Audio File: {file_title}")
    text_results.append(f"Duration: {audio_duration:.2f} seconds")
    text_results.append(f"Sampling Rate: {sr} Hz")
    
    filtered_audio = bandpass_filter(audio, sr, lowcut=2000, highcut=6000)
    cps, frame_times = calculate_cps(filtered_audio, sr, frame_duration=1.0)
    
    # CPS Statistics
    text_results.append("CPS Statistics:")
    text_results.append(f"Average CPS: {np.mean(cps):.2f}")
    text_results.append(f"Maximum CPS: {np.max(cps):.2f}")
    text_results.append(f"Minimum CPS: {np.min(cps):.2f}")
    text_results.append(f"Frames with CPS >= 5: {np.sum(cps >= 5)}")
    text_results.append(f"Frames with CPS >= 10: {np.sum(cps >= 10)}")
    
    # Join text results with newlines, preserving exact format
    text_output = "\n".join(text_results)
    
    # Add text to PDF
    add_text_to_pdf(pdf, text_output)
    
    # Generate and save plot to PDF
    fig = plot_aggregated_cps(frame_times, cps, audio_duration, file_title=file_title)
    pdf.savefig(fig)
    plt.close(fig)

# Process all .wav files and save to PDF
def analyze_folder(folder_path):
    wav_files = [f for f in os.listdir(folder_path) if f.endswith(".wav")]
    if not wav_files:
        print("No .wav files found in the directory.")
        return
    
    # Create PDF
    pdf_path = os.path.join(folder_path, "cps_withoutNoiseRed.pdf")
    with PdfPages(pdf_path) as pdf:
        for wav_file in wav_files:
            file_path = os.path.join(folder_path, wav_file)
            try:
                analyze_cps(file_path, pdf)
                print(f"Processed: {wav_file}")
            except FileNotFoundError:
                print(f"Error: The file {file_path} was not found.")
    
    print(f"\nResults saved to {pdf_path}")

# Example usage
if __name__ == "__main__":
    folder_path = "."  # Current directory
    analyze_folder(folder_path)