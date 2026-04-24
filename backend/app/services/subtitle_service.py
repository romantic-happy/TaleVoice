"""
阿里云字幕生成服务模块

通过阿里云智能语音服务实现视频字幕自动生成
支持SRT、ASS等主流字幕格式导出
实现字幕与音频、视频画面的毫秒级精准对齐

API文档: https://help.aliyun.com/document_detail/90727.html
"""

import hashlib
import hmac
import base64
import datetime
import json
import uuid
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from app.core.config import settings
from app.core.logger import app_logger


class SubtitleFormat(str, Enum):
    """字幕格式枚举"""
    SRT = "srt"
    ASS = "ass"
    VTT = "vtt"
    JSON = "json"


class SubtitleStatus(str, Enum):
    """字幕生成状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubtitleSegment:
    """
    单条字幕数据结构

    Attributes:
        index: 字幕序号
        start_time: 开始时间(毫秒)
        end_time: 结束时间(毫秒)
        text: 字幕文本
        confidence: 识别置信度(0-1)
    """
    index: int
    start_time: int
    end_time: int
    text: str
    confidence: float = 1.0

    def to_srt(self) -> str:
        """转换为SRT格式"""
        start_str = self._ms_to_srt_time(self.start_time)
        end_str = self._ms_to_srt_time(self.end_time)
        return f"{self.index}\n{start_str} --> {end_str}\n{self.text}\n"

    def to_ass(self, style: str = "Default") -> str:
        """转换为ASS格式"""
        start_str = self._ms_to_ass_time(self.start_time)
        end_str = self._ms_to_ass_time(self.end_time)
        return f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{self.text}"

    @staticmethod
    def _ms_to_srt_time(ms: int) -> str:
        """毫秒转SRT时间格式 (00:00:00,000)"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    @staticmethod
    def _ms_to_ass_time(ms: int) -> str:
        """毫秒转ASS时间格式 (0:00:00.00)"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        centiseconds = (ms % 1000) // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


@dataclass
class SubtitleResult:
    """
    字幕生成结果数据结构

    Attributes:
        task_id: 任务ID
        status: 生成状态
        segments: 字幕片段列表
        language: 识别语言
        duration: 音频时长(毫秒)
        format: 字幕格式
        content: 完整字幕内容
        file_url: 字幕文件URL
        error_message: 错误信息
    """
    task_id: str = ""
    status: SubtitleStatus = SubtitleStatus.PENDING
    segments: List[SubtitleSegment] = field(default_factory=list)
    language: str = "zh-CN"
    duration: int = 0
    format: SubtitleFormat = SubtitleFormat.SRT
    content: str = ""
    file_url: Optional[str] = None
    error_message: Optional[str] = None


class AliyunSubtitleService:
    """
    阿里云字幕生成服务

    通过阿里云智能语音交互API实现语音识别和字幕生成
    支持实时语音识别和录音文件识别两种模式
    """

    def __init__(self):
        """初始化字幕服务，从配置读取API密钥和地址"""
        self.access_key_id = getattr(settings, "ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = getattr(settings, "ALIYUN_ACCESS_KEY_SECRET", "")
        self.app_key = getattr(settings, "ALIYUN_SUBTITLE_APP_KEY", "")

        self.api_endpoint = "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr"
        self.file_api_endpoint = "https://filetrans.cn-shanghai.aliyuncs.com/pop/2019-02-28/files"
        self.callback_url = getattr(settings, "ALIYUN_SUBTITLE_CALLBACK_URL", "")

        self._timeout = 300

    def _build_common_params(self) -> Dict[str, str]:
        """
        构建公共请求参数

        Returns:
            Dict[str, str]: 公共参数字典
        """
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        signature_nonce = str(uuid.uuid4())

        return {
            "AccessKeyId": self.access_key_id,
            "Action": "SubmitTask",
            "Format": "JSON",
            "RegionId": "cn-shanghai",
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": signature_nonce,
            "SignatureVersion": "1.0",
            "Timestamp": timestamp,
            "Version": "2019-02-28"
        }

    def _generate_signature(self, params: Dict[str, str]) -> str:
        """
        生成API签名

        Args:
            params: 请求参数字典

        Returns:
            str: 签名字符串
        """
        sorted_params = sorted(params.items())
        canonicalized_query_string = "&".join(
            f"{self._percent_encode(k)}={self._percent_encode(v)}"
            for k, v in sorted_params
        )

        string_to_sign = f"POST&%2F&{self._percent_encode(canonicalized_query_string)}"

        h = hmac.new(
            (self.access_key_secret + "&").encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        )
        signature = base64.b64encode(h.digest()).decode('utf-8')
        return signature

    @staticmethod
    def _percent_encode(s: str) -> str:
        """URL编码"""
        import urllib.parse
        return urllib.parse.quote(s, safe='').replace('+', '%20').replace('*', '%2A').replace('%7E', '~')

    async def submit_file_task(
        self,
        audio_url: str,
        language: str = "zh-CN",
        enable_words: bool = True,
        enable_punctuation: bool = True,
        enable_inverse_text_normalization: bool = True
    ) -> SubtitleResult:
        """
        提交录音文件识别任务

        Args:
            audio_url: 音频文件URL(支持mp3/wav/m4a等格式)
            language: 语言代码(zh-CN/en-US等)
            enable_words: 是否返回词级时间戳
            enable_punctuation: 是否启用智能断句
            enable_inverse_text_normalization: 是否启用数字转换

        Returns:
            SubtitleResult: 包含任务ID的结果
        """
        try:
            import httpx

            params = self._build_common_params()
            params["AppKey"] = self.app_key
            params["FileLink"] = audio_url
            params["Version"] = "4.0"

            if self.callback_url:
                params["Callback"] = self.callback_url

            params["Signature"] = self._generate_signature(params)

            app_logger.info(f"[AliyunSubtitleService] 提交字幕生成任务: {audio_url}")

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self.file_api_endpoint,
                    data=params
                )
                response.raise_for_status()
                data = response.json()

            if data.get("StatusCode") != 21050000:
                error_msg = data.get("StatusText", "未知错误")
                app_logger.error(f"[AliyunSubtitleService] 任务提交失败: {error_msg}")
                return SubtitleResult(
                    status=SubtitleStatus.FAILED,
                    error_message=error_msg
                )

            task_id = data.get("TaskId", "")
            app_logger.info(f"[AliyunSubtitleService] 任务已提交: {task_id}")

            return SubtitleResult(
                task_id=task_id,
                status=SubtitleStatus.PROCESSING,
                language=language
            )

        except ImportError:
            app_logger.error("[AliyunSubtitleService] httpx未安装")
            return SubtitleResult(
                status=SubtitleStatus.FAILED,
                error_message="httpx未安装，请执行 pip install httpx"
            )
        except Exception as e:
            app_logger.error(f"[AliyunSubtitleService] 任务提交失败: {str(e)}")
            return SubtitleResult(
                status=SubtitleStatus.FAILED,
                error_message=str(e)
            )

    async def query_task_status(self, task_id: str) -> SubtitleResult:
        """
        查询字幕生成任务状态

        Args:
            task_id: 任务ID

        Returns:
            SubtitleResult: 当前任务状态和结果
        """
        try:
            import httpx

            params = self._build_common_params()
            params["Action"] = "GetTaskResult"
            params["TaskId"] = task_id
            params["Signature"] = self._generate_signature(params)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.file_api_endpoint,
                    data=params
                )
                response.raise_for_status()
                data = response.json()

            status_code = data.get("StatusCode", 0)

            if status_code == 21050000:
                return SubtitleResult(
                    task_id=task_id,
                    status=SubtitleStatus.PROCESSING
                )

            if status_code == 21050002:
                result = self._parse_result(data)
                result.task_id = task_id
                result.status = SubtitleStatus.COMPLETED
                return result

            if status_code == 21050003:
                error_msg = data.get("StatusText", "识别失败")
                return SubtitleResult(
                    task_id=task_id,
                    status=SubtitleStatus.FAILED,
                    error_message=error_msg
                )

            return SubtitleResult(
                task_id=task_id,
                status=SubtitleStatus.PENDING
            )

        except Exception as e:
            app_logger.error(f"[AliyunSubtitleService] 查询任务状态失败: {str(e)}")
            return SubtitleResult(
                task_id=task_id,
                status=SubtitleStatus.FAILED,
                error_message=str(e)
            )

    def _parse_result(self, data: Dict[str, Any]) -> SubtitleResult:
        """
        解析识别结果

        Args:
            data: API返回的数据

        Returns:
            SubtitleResult: 解析后的结果
        """
        result = SubtitleResult()
        result.language = data.get("Result", {}).get("Language", "zh-CN")

        sentences = data.get("Result", {}).get("Sentences", [])
        segments = []

        for idx, sentence in enumerate(sentences, 1):
            segment = SubtitleSegment(
                index=idx,
                start_time=int(sentence.get("BeginTime", 0)),
                end_time=int(sentence.get("EndTime", 0)),
                text=sentence.get("Text", ""),
                confidence=sentence.get("Confidence", 1.0)
            )
            segments.append(segment)

        result.segments = segments
        result.duration = segments[-1].end_time if segments else 0

        return result

    def export_subtitle(
        self,
        result: SubtitleResult,
        format: SubtitleFormat = SubtitleFormat.SRT,
        output_path: Optional[str] = None
    ) -> str:
        """
        导出字幕文件

        Args:
            result: 字幕生成结果
            format: 字幕格式
            output_path: 输出文件路径，None则自动生成

        Returns:
            str: 字幕文件路径或内容
        """
        if format == SubtitleFormat.SRT:
            content = self._export_srt(result.segments)
        elif format == SubtitleFormat.ASS:
            content = self._export_ass(result.segments)
        elif format == SubtitleFormat.VTT:
            content = self._export_vtt(result.segments)
        elif format == SubtitleFormat.JSON:
            content = self._export_json(result.segments)
        else:
            content = self._export_srt(result.segments)

        result.content = content
        result.format = format

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            app_logger.info(f"[AliyunSubtitleService] 字幕已保存: {output_path}")
            return output_path

        return content

    def _export_srt(self, segments: List[SubtitleSegment]) -> str:
        """导出SRT格式字幕"""
        return "\n".join(seg.to_srt() for seg in segments)

    def _export_ass(self, segments: List[SubtitleSegment]) -> str:
        """导出ASS格式字幕"""
        header = """[Script Info]
Title: TaleVoice Subtitle
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        dialogues = "\n".join(seg.to_ass() for seg in segments)
        return header + dialogues

    def _export_vtt(self, segments: List[SubtitleSegment]) -> str:
        """导出VTT格式字幕"""
        header = "WEBVTT\n\n"
        content = ""
        for seg in segments:
            start = seg._ms_to_srt_time(seg.start_time).replace(",", ".")
            end = seg._ms_to_srt_time(seg.end_time).replace(",", ".")
            content += f"{start} --> {end}\n{seg.text}\n\n"
        return header + content

    def _export_json(self, segments: List[SubtitleSegment]) -> str:
        """导出JSON格式字幕"""
        data = {
            "segments": [
                {
                    "index": seg.index,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "text": seg.text,
                    "confidence": seg.confidence
                }
                for seg in segments
            ]
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    async def generate_subtitle_from_video(
        self,
        video_url: str,
        format: SubtitleFormat = SubtitleFormat.SRT,
        language: str = "zh-CN",
        output_path: Optional[str] = None,
        max_wait_seconds: int = 300
    ) -> SubtitleResult:
        """
        从视频生成字幕（完整流程）

        Args:
            video_url: 视频文件URL
            format: 字幕格式
            language: 语言代码
            output_path: 输出路径
            max_wait_seconds: 最大等待时间(秒)

        Returns:
            SubtitleResult: 字幕生成结果
        """
        import asyncio

        submit_result = await self.submit_file_task(video_url, language)
        if submit_result.status == SubtitleStatus.FAILED:
            return submit_result

        task_id = submit_result.task_id
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_seconds:
                return SubtitleResult(
                    task_id=task_id,
                    status=SubtitleStatus.FAILED,
                    error_message="任务超时"
                )

            await asyncio.sleep(3)

            result = await self.query_task_status(task_id)
            if result.status == SubtitleStatus.COMPLETED:
                self.export_subtitle(result, format, output_path)
                return result

            if result.status == SubtitleStatus.FAILED:
                return result


subtitle_service = AliyunSubtitleService()
