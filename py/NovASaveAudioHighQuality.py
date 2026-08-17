import os
import struct
import wave
from datetime import datetime
import torch
import folder_paths


class NovASaveAudioWav:
    """
    Custom ComfyUI node to export audio latents to uncompressed WAV formats
    with numerical timestamping (DDHHMMSS) in the filename.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename_prefix": ("STRING", {"default": "audio/NovA_Audio"}),
                "audio_format": (
                    [
                        "PCM 24-bit (Studio)",
                        "Float 32-bit (Bit-Exact VAE)",
                        "PCM 16-bit (CD Quality)",
                        "PCM 32-bit Integer",
                    ],
                    {"default": "PCM 24-bit (Studio)"},
                ),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_audio_wav"
    OUTPUT_NODE = True
    CATEGORY = "️☣️ NovA/Audio"

    def _write_ieee_float32_wav(self, file_path, waveform_np, sample_rate, channels):
        """Writes IEEE 754 Float 32-bit uncompressed WAV file directly to disk."""
        data_bytes = waveform_np.tobytes()
        data_size = len(data_bytes)
        bytes_per_sample = 4
        block_align = channels * bytes_per_sample
        byte_rate = sample_rate * block_align

        # Construct RIFF WAV header for IEEE Float (Format code 3)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,  # Subchunk1Size for PCM/Float
            3,   # AudioFormat: 3 = IEEE Float
            channels,
            sample_rate,
            byte_rate,
            block_align,
            32,  # BitsPerSample
            b"data",
            data_size,
        )

        with open(file_path, "wb") as f:
            f.write(header)
            f.write(data_bytes)

    def save_audio_wav(
        self,
        audio,
        filename_prefix="audio/NovA_Audio",
        audio_format="PCM 24-bit (Studio)",
    ):
        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])

        # Normalize batch dimension [batch, channels, samples] -> [channels, samples]
        if waveform.dim() == 3:
            waveform = waveform[0]

        waveform = waveform.detach().cpu()
        channels, _ = waveform.shape

        # Generate numerical timestamp string: Day (DD), Hour (HH), Minute (MM), Second (SS)
        timestamp = datetime.now().strftime("%d%H%M%S")

        # Parse folder prefix and base filename
        subfolder, base_name = os.path.split(filename_prefix)

        # Build filename with timestamp
        formatted_filename = f"{base_name}-{timestamp}.wav"

        # Resolve destination output directory
        output_dir = folder_paths.get_output_directory()
        full_output_folder = os.path.join(output_dir, subfolder)
        os.makedirs(full_output_folder, exist_ok=True)
        file_path = os.path.join(full_output_folder, formatted_filename)

        if audio_format == "Float 32-bit (Bit-Exact VAE)":
            # Interleave channels for float32 raw data: [channels, samples] -> [samples, channels]
            interleaved_float = waveform.t().contiguous().numpy().astype("float32")
            self._write_ieee_float32_wav(file_path, interleaved_float, sample_rate, channels)

        else:
            # Handle integer PCM quantization formats
            waveform = torch.clamp(waveform, -1.0, 1.0)

            if audio_format == "PCM 16-bit (CD Quality)":
                int_samples = (waveform * 32767.0).to(torch.int16)
                sampwidth = 2
            elif audio_format == "PCM 32-bit Integer":
                int_samples = (waveform * 2147483647.0).to(torch.int32)
                sampwidth = 4
            elif audio_format == "PCM 24-bit (Studio)":
                int_samples = (waveform * 8388607.0).to(torch.int32)
                sampwidth = 3

            interleaved = int_samples.t().contiguous().numpy()

            with wave.open(file_path, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sampwidth)
                wav_file.setframerate(sample_rate)

                if audio_format == "PCM 24-bit (Studio)":
                    # Pack 24-bit integers into 3 bytes per sample
                    raw_bytes = bytearray()
                    for sample in interleaved.flat:
                        raw_bytes.extend(int(sample).to_bytes(3, byteorder="little", signed=True))
                    wav_file.writeframes(bytes(raw_bytes))
                else:
                    wav_file.writeframes(interleaved.tobytes())

        return {
            "ui": {
                "audio": [
                    {
                        "filename": formatted_filename,
                        "subfolder": subfolder,
                        "type": "output",
                    }
                ]
            }
        }


NODE_CLASS_MAPPINGS = {"NovASaveAudioWav": NovASaveAudioWav}
NODE_DISPLAY_NAME_MAPPINGS = {"NovASaveAudioWav": "NovA Save Audio High Quality"}