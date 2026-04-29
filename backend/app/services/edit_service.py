"""
阿里云智能剪辑服务模块

通过阿里云IMS智能媒体服务实现视频智能剪辑
支持多段视频拼接、转场效果、滤镜、背景音乐处理

API文档: https://help.aliyun.com/document_detail/197842.html
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


class TransitionType(str, Enum):
    """转场效果类型枚举"""
    FADE = "fade"
    DISSOLVE = "dissolve"
    WIPE_LEFT = "wipe_left"
    WIPE_RIGHT = "wipe_right"
    WIPE_UP = "wipe_up"
    WIPE_DOWN = "wipe_down"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    ROTATE = "rotate"
    BLUR = "blur"


class FilterType(str, Enum):
    """滤镜效果类型枚举"""
    NONE = "none"
    WARM = "warm"
    COOL = "cool"
    VINTAGE = "vintage"
    BLACK_WHITE = "black_white"
    SEPIA = "sepia"
    BRIGHT = "bright"
    CONTRAST = "contrast"
    SATURATE = "saturate"
    SHARPEN = "sharpen"


class EditTaskStatus(str, Enum):
    """剪辑任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class VideoClip:
    """
    视频片段数据结构

    Attributes:
        video_url: 视频文件URL
        start_time: 片段开始时间(秒)
        end_time: 片段结束时间(秒)
        duration: 片段时长(秒)
        transition_in: 入场转场效果
        transition_out: 出场转场效果
        transition_duration: 转场时长(秒)
        filter_type: 滤镜类型
        volume: 音量(0-100)
    """
    video_url: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    transition_in: TransitionType = TransitionType.FADE
    transition_out: TransitionType = TransitionType.FADE
    transition_duration: float = 0.5
    filter_type: FilterType = FilterType.NONE
    volume: int = 100


@dataclass
class BackgroundMusic:
    """
    背景音乐数据结构

    Attributes:
        music_url: 音乐文件URL
        volume: 音量(0-100)
        fade_in: 淡入时长(秒)
        fade_out: 淡出时长(秒)
        loop: 是否循环
        start_time: 开始播放时间(秒)
    """
    music_url: str
    volume: int = 30
    fade_in: float = 1.0
    fade_out: float = 1.5
    loop: bool = True
    start_time: float = 0.0


@dataclass
class EditTimeline:
    """
    剪辑时间线数据结构

    Attributes:
        clips: 视频片段列表
        bgm: 背景音乐配置
        total_duration: 总时长(秒)
        resolution: 输出分辨率
        fps: 输出帧率
    """
    clips: List[VideoClip] = field(default_factory=list)
    bgm: Optional[BackgroundMusic] = None
    total_duration: float = 0.0
    resolution: str = "1920x1080"
    fps: int = 30


@dataclass
class EditResult:
    """
    剪辑任务结果数据结构

    Attributes:
        task_id: 任务ID
        status: 任务状态
        output_url: 输出视频URL
        duration: 输出视频时长(秒)
        file_size: 文件大小(字节)
        resolution: 分辨率
        fps: 帧率
        error_message: 错误信息
    """
    task_id: str = ""
    status: EditTaskStatus = EditTaskStatus.PENDING
    output_url: Optional[str] = None
    duration: float = 0.0
    file_size: int = 0
    resolution: str = "1920x1080"
    fps: int = 30
    error_message: Optional[str] = None


class AliyunEditService:
    """
    阿里云智能剪辑服务

    通过阿里云IMS智能媒体服务API实现视频剪辑
    支持多段视频拼接、转场效果、滤镜、背景音乐处理
    """

    TRANSITION_EFFECTS = {
        TransitionType.FADE: {"Type": "Fade", "Duration": 0.5},
        TransitionType.DISSOLVE: {"Type": "Dissolve", "Duration": 0.5},
        TransitionType.WIPE_LEFT: {"Type": "Wipe", "Direction": "Left", "Duration": 0.5},
        TransitionType.WIPE_RIGHT: {"Type": "Wipe", "Direction": "Right", "Duration": 0.5},
        TransitionType.WIPE_UP: {"Type": "Wipe", "Direction": "Up", "Duration": 0.5},
        TransitionType.WIPE_DOWN: {"Type": "Wipe", "Direction": "Down", "Duration": 0.5},
        TransitionType.SLIDE_LEFT: {"Type": "Slide", "Direction": "Left", "Duration": 0.5},
        TransitionType.SLIDE_RIGHT: {"Type": "Slide", "Direction": "Right", "Duration": 0.5},
        TransitionType.ZOOM_IN: {"Type": "Zoom", "Mode": "In", "Duration": 0.5},
        TransitionType.ZOOM_OUT: {"Type": "Zoom", "Mode": "Out", "Duration": 0.5},
        TransitionType.ROTATE: {"Type": "Rotate", "Duration": 0.5},
        TransitionType.BLUR: {"Type": "Blur", "Duration": 0.5}
    }

    FILTER_EFFECTS = {
        FilterType.NONE: {},
        FilterType.WARM: {"ColorTemperature": 6500, "Saturation": 1.1},
        FilterType.COOL: {"ColorTemperature": 4500, "Saturation": 1.0},
        FilterType.VINTAGE: {"Saturation": 0.8, "Contrast": 1.1, "Vignette": 0.3},
        FilterType.BLACK_WHITE: {"Saturation": 0.0},
        FilterType.SEPIA: {"Saturation": 0.5, "ColorTemperature": 5500},
        FilterType.BRIGHT: {"Brightness": 1.2},
        FilterType.CONTRAST: {"Contrast": 1.3},
        FilterType.SATURATE: {"Saturation": 1.5},
        FilterType.SHARPEN: {"Sharpen": 0.5}
    }

    def __init__(self):
        """初始化剪辑服务，从配置读取API密钥和地址"""
        self.access_key_id = getattr(settings, "ALIYUN_ACCESS_KEY_ID", "")
        self.access_key_secret = getattr(settings, "ALIYUN_ACCESS_KEY_SECRET", "")
        self.region_id = getattr(settings, "ALIYUN_EDIT_REGION", "cn-shanghai")

        self.api_endpoint = f"https://ims.{self.region_id}.aliyuncs.com"
        self.callback_url = getattr(settings, "ALIYUN_EDIT_CALLBACK_URL", "")

        self._timeout = 600

    def _build_common_params(self, action: str) -> Dict[str, str]:
        """
        构建公共请求参数

        Args:
            action: API操作名称

        Returns:
            Dict[str, str]: 公共参数字典
        """
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        signature_nonce = str(uuid.uuid4())

        return {
            "AccessKeyId": self.access_key_id,
            "Action": action,
            "Format": "JSON",
            "RegionId": self.region_id,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": signature_nonce,
            "SignatureVersion": "1.0",
            "Timestamp": timestamp,
            "Version": "2017-09-01"
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
            f"{self._percent_encode(k)}={self._percent_encode(str(v))}"
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

    def _build_timeline_config(self, timeline: EditTimeline) -> Dict[str, Any]:
        """
        构建时间线配置

        Args:
            timeline: 时间线数据

        Returns:
            Dict[str, Any]: 时间线配置字典
        """
        tracks = []
        video_track = {
            "Type": "Video",
            "TrackClips": []
        }

        for idx, clip in enumerate(timeline.clips):
            track_clip = {
                "MediaURL": clip.video_url,
                "Type": "Video",
                "TimelineIn": sum(c.duration for c in timeline.clips[:idx]),
                "TimelineOut": sum(c.duration for c in timeline.clips[:idx + 1]),
                "In": clip.start_time,
                "Out": clip.end_time if clip.end_time > 0 else clip.duration
            }

            if clip.transition_in != TransitionType.FADE or idx > 0:
                transition = self.TRANSITION_EFFECTS.get(clip.transition_in, {})
                if transition:
                    track_clip["TransitionIn"] = transition.get("Type", "Fade")
                    track_clip["TransitionInDuration"] = clip.transition_duration

            if clip.filter_type != FilterType.NONE:
                filter_config = self.FILTER_EFFECTS.get(clip.filter_type, {})
                if filter_config:
                    track_clip["Effects"] = [filter_config]

            video_track["TrackClips"].append(track_clip)

        tracks.append(video_track)

        if timeline.bgm:
            audio_track = {
                "Type": "Audio",
                "TrackClips": [{
                    "MediaURL": timeline.bgm.music_url,
                    "Type": "Audio",
                    "TimelineIn": timeline.bgm.start_time,
                    "TimelineOut": timeline.total_duration if timeline.total_duration > 0 else sum(c.duration for c in timeline.clips),
                    "Volume": timeline.bgm.volume / 100.0,
                    "FadeInDuration": timeline.bgm.fade_in,
                    "FadeOutDuration": timeline.bgm.fade_out
                }]
            }
            if timeline.bgm.loop:
                audio_track["TrackClips"][0]["LoopMode"] = "Repeat"
            tracks.append(audio_track)

        return {
            "VideoTracks": [video_track],
            "AudioTracks": [audio_track] if timeline.bgm else [],
            "OutputMediaConfig": {
                "Width": int(timeline.resolution.split("x")[0]),
                "Height": int(timeline.resolution.split("x")[1]),
                "FPS": timeline.fps,
                "Bitrate": 5000
            }
        }

    async def submit_edit_task(
        self,
        timeline: EditTimeline,
        output_bucket: str,
        output_object: str,
        output_format: str = "mp4"
    ) -> EditResult:
        """
        提交智能剪辑任务

        Args:
            timeline: 剪辑时间线配置
            output_bucket: 输出OSS Bucket
            output_object: 输出OSS Object路径
            output_format: 输出格式(mp4/mov等)

        Returns:
            EditResult: 包含任务ID的结果
        """
        try:
            import httpx

            params = self._build_common_params("SubmitMediaProducingJob")

            timeline_config = self._build_timeline_config(timeline)

            params["Timeline"] = json.dumps(timeline_config, ensure_ascii=False)
            params["OutputMediaConfig"] = json.dumps({
                "MediaURL": f"oss://{output_bucket}/{output_object}",
                "Type": "Video",
                "Format": output_format
            }, ensure_ascii=False)

            if self.callback_url:
                params["UserData"] = json.dumps({"Callback": self.callback_url})

            params["Signature"] = self._generate_signature(params)

            app_logger.info(f"[AliyunEditService] 提交剪辑任务，片段数: {len(timeline.clips)}")

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self.api_endpoint,
                    data=params
                )
                response.raise_for_status()
                data = response.json()

            if "JobId" not in data:
                error_msg = data.get("Message", "未知错误")
                app_logger.error(f"[AliyunEditService] 任务提交失败: {error_msg}")
                return EditResult(
                    status=EditTaskStatus.FAILED,
                    error_message=error_msg
                )

            task_id = data["JobId"]
            app_logger.info(f"[AliyunEditService] 剪辑任务已提交: {task_id}")

            return EditResult(
                task_id=task_id,
                status=EditTaskStatus.PROCESSING
            )

        except ImportError:
            app_logger.error("[AliyunEditService] httpx未安装")
            return EditResult(
                status=EditTaskStatus.FAILED,
                error_message="httpx未安装，请执行 pip install httpx"
            )
        except Exception as e:
            app_logger.error(f"[AliyunEditService] 任务提交失败: {str(e)}")
            return EditResult(
                status=EditTaskStatus.FAILED,
                error_message=str(e)
            )

    async def query_task_status(self, task_id: str) -> EditResult:
        """
        查询剪辑任务状态

        Args:
            task_id: 任务ID

        Returns:
            EditResult: 当前任务状态和结果
        """
        try:
            import httpx

            params = self._build_common_params("GetMediaProducingJob")
            params["JobId"] = task_id
            params["Signature"] = self._generate_signature(params)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.api_endpoint,
                    data=params
                )
                response.raise_for_status()
                data = response.json()

            status = data.get("Status", "Unknown")

            status_map = {
                "Init": EditTaskStatus.PENDING,
                "Analyzing": EditTaskStatus.PROCESSING,
                "Producing": EditTaskStatus.PROCESSING,
                "Success": EditTaskStatus.COMPLETED,
                "Failed": EditTaskStatus.FAILED
            }

            mapped_status = status_map.get(status, EditTaskStatus.PENDING)

            result = EditResult(
                task_id=task_id,
                status=mapped_status
            )

            if mapped_status == EditTaskStatus.COMPLETED:
                output = data.get("OutputMedia", {})
                result.output_url = output.get("MediaURL", "")
                result.duration = output.get("Duration", 0)
                result.file_size = output.get("Size", 0)
                result.resolution = f"{output.get('Width', 1920)}x{output.get('Height', 1080)}"
                result.fps = output.get("FPS", 30)

            if mapped_status == EditTaskStatus.FAILED:
                result.error_message = data.get("ErrorCode", "") + ": " + data.get("ErrorMsg", "剪辑失败")

            return result

        except Exception as e:
            app_logger.error(f"[AliyunEditService] 查询任务状态失败: {str(e)}")
            return EditResult(
                task_id=task_id,
                status=EditTaskStatus.FAILED,
                error_message=str(e)
            )

    async def merge_videos(
        self,
        video_urls: List[str],
        output_bucket: str,
        output_object: str,
        transition: TransitionType = TransitionType.FADE,
        transition_duration: float = 0.5,
        filter_type: FilterType = FilterType.NONE,
        bgm_url: Optional[str] = None,
        bgm_volume: int = 30,
        bgm_fade_in: float = 1.0,
        bgm_fade_out: float = 1.5,
        resolution: str = "1920x1080",
        fps: int = 30
    ) -> EditResult:
        """
        合并多个视频（便捷方法）

        Args:
            video_urls: 视频URL列表
            output_bucket: 输出OSS Bucket
            output_object: 输出OSS Object路径
            transition: 转场效果
            transition_duration: 转场时长
            filter_type: 滤镜类型
            bgm_url: 背景音乐URL
            bgm_volume: 背景音乐音量
            bgm_fade_in: 淡入时长
            bgm_fade_out: 淡出时长
            resolution: 输出分辨率
            fps: 输出帧率

        Returns:
            EditResult: 剪辑结果
        """
        clips = []
        for url in video_urls:
            clip = VideoClip(
                video_url=url,
                transition_in=transition,
                transition_out=transition,
                transition_duration=transition_duration,
                filter_type=filter_type
            )
            clips.append(clip)

        bgm = None
        if bgm_url:
            bgm = BackgroundMusic(
                music_url=bgm_url,
                volume=bgm_volume,
                fade_in=bgm_fade_in,
                fade_out=bgm_fade_out
            )

        timeline = EditTimeline(
            clips=clips,
            bgm=bgm,
            resolution=resolution,
            fps=fps
        )

        return await self.submit_edit_task(timeline, output_bucket, output_object)

    async def edit_with_full_control(
        self,
        timeline: EditTimeline,
        output_bucket: str,
        output_object: str,
        max_wait_seconds: int = 600
    ) -> EditResult:
        """
        完全控制的剪辑方法（等待完成）

        Args:
            timeline: 时间线配置
            output_bucket: 输出OSS Bucket
            output_object: 输出OSS Object路径
            max_wait_seconds: 最大等待时间(秒)

        Returns:
            EditResult: 剪辑结果
        """
        import asyncio

        submit_result = await self.submit_edit_task(timeline, output_bucket, output_object)
        if submit_result.status == EditTaskStatus.FAILED:
            return submit_result

        task_id = submit_result.task_id
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_seconds:
                return EditResult(
                    task_id=task_id,
                    status=EditTaskStatus.FAILED,
                    error_message="任务超时"
                )

            await asyncio.sleep(5)

            result = await self.query_task_status(task_id)
            if result.status == EditTaskStatus.COMPLETED:
                return result

            if result.status == EditTaskStatus.FAILED:
                return result

    def get_available_transitions(self) -> List[Dict[str, str]]:
        """
        获取可用的转场效果列表

        Returns:
            List[Dict[str, str]]: 转场效果列表
        """
        return [
            {"type": t.value, "name": self._get_transition_name(t)}
            for t in TransitionType
        ]

    def get_available_filters(self) -> List[Dict[str, str]]:
        """
        获取可用的滤镜效果列表

        Returns:
            List[Dict[str, str]]: 滤镜效果列表
        """
        return [
            {"type": f.value, "name": self._get_filter_name(f)}
            for f in FilterType
        ]

    @staticmethod
    def _get_transition_name(transition: TransitionType) -> str:
        """获取转场效果中文名称"""
        names = {
            TransitionType.FADE: "淡入淡出",
            TransitionType.DISSOLVE: "溶解",
            TransitionType.WIPE_LEFT: "向左擦除",
            TransitionType.WIPE_RIGHT: "向右擦除",
            TransitionType.WIPE_UP: "向上擦除",
            TransitionType.WIPE_DOWN: "向下擦除",
            TransitionType.SLIDE_LEFT: "向左滑动",
            TransitionType.SLIDE_RIGHT: "向右滑动",
            TransitionType.ZOOM_IN: "放大",
            TransitionType.ZOOM_OUT: "缩小",
            TransitionType.ROTATE: "旋转",
            TransitionType.BLUR: "模糊"
        }
        return names.get(transition, transition.value)

    @staticmethod
    def _get_filter_name(filter_type: FilterType) -> str:
        """获取滤镜效果中文名称"""
        names = {
            FilterType.NONE: "无滤镜",
            FilterType.WARM: "暖色调",
            FilterType.COOL: "冷色调",
            FilterType.VINTAGE: "复古",
            FilterType.BLACK_WHITE: "黑白",
            FilterType.SEPIA: "怀旧",
            FilterType.BRIGHT: "明亮",
            FilterType.CONTRAST: "高对比度",
            FilterType.SATURATE: "高饱和度",
            FilterType.SHARPEN: "锐化"
        }
        return names.get(filter_type, filter_type.value)


edit_service = AliyunEditService()
