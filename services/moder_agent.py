from transformers import pipeline, CLIPProcessor, CLIPModel
import torch
from PIL import Image
import io
import av
import numpy as np
import librosa

from config import config


class ModerAgent:
    def __init__(self, text_model: str, image_model: str):
        self.device = 0 if torch.cuda.is_available() else -1
        self.pipe = pipeline("text-classification", model=text_model, device=self.device)

        self.model = CLIPModel.from_pretrained(image_model)
        if self.device == 0:
            self.model.to("cuda")
        self.processor = CLIPProcessor.from_pretrained(image_model)

        self.voice_pipe = pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small",
            device=self.device
        )


    def process_text(self, text: str):
        result = self.pipe(text)[0]
        return result["label"] == "toxic" and result["score"] > 0.8


    def _analyze_image(self, pil_image: Image):
        bad_labels = [
            "pornographic nude image",
            "sexual explicit content",
            "violent bloody scene",
            "offensive meme with insults",
            "image containing swear words",
            "toxic internet meme",
            "harassment or bullying meme"
        ]

        good_labels = [
            "normal harmless image",
            "family friendly photo",
            "clean internet meme",
            "screenshot of programming code",
            "friendly chat screenshot"
        ]

        labels = bad_labels + good_labels

        inputs = self.processor(text=labels, images=pil_image, return_tensors="pt", padding=True)
        if self.device == 0:
            inputs = {k: v.to("cuda") for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)
        max_prob, idx = torch.max(probs, dim=1)
        print(labels[idx], max_prob.item())
        return idx.item() < len(bad_labels) and max_prob.item() > 0.25


    def process_image(self, image_bytes: io.BytesIO) -> bool:
        image_bytes.seek(0)
        img = Image.open(image_bytes)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        else:
            img = img.convert("RGB")

        return self._analyze_image(img)


    def process_gif(self, gif_bytes: io.BytesIO) -> bool:
        gif_bytes.seek(0)
        try:
            container = av.open(gif_bytes)
            stream = container.streams.video[0]

            total_frames = stream.frames
            if total_frames <= 0:
                total_frames = 100

            target_indices = {0, total_frames // 2, max(0, total_frames - 1)}

            found_bad = False
            frame_count = 0

            for frame in container.decode(video=0):
                if frame_count in target_indices:
                    img = frame.to_image().convert("RGB")

                    if self._analyze_image(img):
                        found_bad = True
                        break

                frame_count += 1
                if frame_count > max(target_indices):
                    break

            container.close()
            return found_bad

        except Exception as e:
            print(f"Ошибка при глубоком анализе гифки: {e}")
            return False


    def process_voice(self, voice_bytes: io.BytesIO) -> bool:
        voice_bytes.seek(0)
        try:
            container = av.open(voice_bytes)
            stream = container.streams.audio[0]

            resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)

            audio_frames = []
            for frame in container.decode(stream):
                resampled_frames = resampler.resample(frame)
                for rf in resampled_frames:
                    audio_frames.append(rf.to_ndarray().flatten())

            if not audio_frames:
                return False

            audio_data = np.concatenate(audio_frames).astype(np.float32) / 32768.0

            container.close()

            result = self.voice_pipe(audio_data)
            transcribed_text = result.get("text", "")

            if transcribed_text.strip():
                print(f"Распознано: {transcribed_text}")
                return self.process_text(transcribed_text)

            return False

        except Exception as e:
            print(f"Ошибка обработки аудио через AV: {e}")
            return False


moder_agent = ModerAgent(config.TEXT_MODEL, config.IMAGE_MODEL)