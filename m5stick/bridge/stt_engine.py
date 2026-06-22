"""
STT (语音转文字) 引擎

支持 Vosk 离线识别和 Whisper 离线识别。
复用 m4a_to_md 的 Vosk 模型和配置模式。
"""

import json
import wave
import asyncio
import logging
from pathlib import Path
from typing import Optional
from .config import STT_CONFIG

logger = logging.getLogger(__name__)


class STTResult:
    """语音识别结果。"""

    def __init__(self, text: str, confidence: float = 0.0, partial: bool = False):
        self.text = text
        self.confidence = confidence
        self.partial = partial

    def __bool__(self):
        return bool(self.text.strip())

    def __repr__(self):
        status = "partial" if self.partial else "final"
        return f"STTResult('{self.text}', conf={self.confidence:.2f}, {status})"


class STTEngine:
    """
    语音识别引擎封装。

    使用方式:
        engine = STTEngine("vosk")
        result = await engine.transcribe(wav_data)
    """

    def __init__(self, engine: str = None):
        self.engine_name = engine or STT_CONFIG["engine"]
        self._model = None
        self._recognizer = None
        self._loaded = False

    async def load(self) -> bool:
        """
        加载识别模型。

        首次使用可能需要下载模型。
        """
        if self._loaded:
            return True

        if self.engine_name == "vosk":
            return await self._load_vosk()
        elif self.engine_name == "whisper":
            return await self._load_whisper()
        else:
            logger.error(f"不支持的引擎: {self.engine_name}")
            return False

    async def _load_vosk(self) -> bool:
        try:
            import vosk
        except ImportError:
            logger.error("Vosk 未安装: pip install vosk")
            return False

        model_dir = Path(STT_CONFIG["vosk"]["model_dir"])
        model_name = STT_CONFIG["vosk"]["model_name"]
        model_path = model_dir / model_name

        # 搜索存在的模型目录
        if not model_path.exists():
            logger.info(f"模型路径不存在: {model_path}")
            # 尝试查找任何模型目录
            found = list(model_dir.glob("vosk-model-*"))
            if found:
                model_path = found[0]
                logger.info(f"使用已存在的模型: {model_path}")
            else:
                logger.error(
                    f"Vosk 中文模型未找到。请下载: \n"
                    f"  wget {STT_CONFIG['vosk']['model_url']}\n"
                    f"  unzip -d {model_dir} {model_name}.zip"
                )
                return False

        try:
            self._model = vosk.Model(str(model_path))
            sample_rate = STT_CONFIG["sample_rate"]
            self._recognizer = vosk.KaldiRecognizer(self._model, sample_rate)
            self._loaded = True
            logger.info(f"Vosk 模型已加载: {model_path.name}")
            return True
        except Exception as e:
            logger.error(f"Vosk 模型加载失败: {e}")
            return False

    async def _load_whisper(self) -> bool:
        try:
            import whisper
        except ImportError:
            logger.error("Whisper 未安装: pip install openai-whisper")
            return False

        model_size = STT_CONFIG["whisper"]["model_size"]
        device = STT_CONFIG["whisper"]["device"]
        try:
            logger.info(f"加载 Whisper {model_size} 模型 (首次使用会下载)...")
            self._model = whisper.load_model(model_size, device=device)
            self._loaded = True
            logger.info("Whisper 模型已加载")
            return True
        except Exception as e:
            logger.error(f"Whisper 模型加载失败: {e}")
            return False

    async def transcribe(self, pcm_data: bytes, sample_rate: int = None) -> Optional[STTResult]:
        """
        转录音频 PCM 数据。

        Args:
            pcm_data: 16-bit 16kHz 单声道 PCM 数据
            sample_rate: 采样率，默认用配置值

        Returns:
            STTResult 或 None (识别失败)
        """
        if not self._loaded:
            logger.info("模型尚未加载，自动加载...")
            loaded = await self.load()
            if not loaded:
                return None

        if sample_rate is None:
            sample_rate = STT_CONFIG["sample_rate"]

        # 运行在 executor 中避免阻塞
        loop = asyncio.get_event_loop()

        if self.engine_name == "vosk":
            return await loop.run_in_executor(
                None, self._transcribe_vosk, pcm_data
            )
        elif self.engine_name == "whisper":
            return await loop.run_in_executor(
                None, self._transcribe_whisper, pcm_data, sample_rate
            )
        return None

    def _transcribe_vosk(self, pcm_data: bytes) -> Optional[STTResult]:
        """同步 Vosk 转录。"""
        if not self._recognizer:
            return None

        self._recognizer.AcceptWaveform(pcm_data)
        result_json = self._recognizer.FinalResult()
        try:
            result = json.loads(result_json)
            text = result.get("text", "").strip()
            if text:
                return STTResult(text=text, confidence=1.0, partial=False)
            return None
        except json.JSONDecodeError:
            logger.warning(f"Vosk 结果解析失败: {result_json[:100]}")
            return None

    def _transcribe_whisper(self, pcm_data: bytes,
                            sample_rate: int) -> Optional[STTResult]:
        """同步 Whisper 转录。"""
        import numpy as np

        # PCM 转 numpy float32 数组
        samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0

        language = STT_CONFIG.get("language", "zh")
        try:
            result = self._model.transcribe(
                samples,
                language=language,
                fp16=False,
            )
            text = result.get("text", "").strip()
            if text:
                return STTResult(text=text, confidence=1.0, partial=False)
            return None
        except Exception as e:
            logger.error(f"Whisper 转录失败: {e}")
            return None

    def reset(self):
        """重置识别器状态（Vosk 需要调用此方法开始新一段识别）。"""
        if self.engine_name == "vosk" and self._model:
            sample_rate = STT_CONFIG["sample_rate"]
            self._recognizer = vosk.KaldiRecognizer(self._model, sample_rate)
