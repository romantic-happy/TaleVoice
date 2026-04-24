"""
背景音乐处理服务

提供背景音乐的上传验证、音量调节、混音处理、Ducking语音避让等功能
基于FFmpeg实现音频处理
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple

from app.core.logger import app_logger


BGM_ALLOWED_FORMATS = {"mp3", "wav", "aac", "ogg", "flac", "m4a"}
BGM_MAX_FILE_SIZE = 20 * 1024 * 1024
BGM_MIN_DURATION = 10
BGM_MAX_DURATION = 600
BGM_DEFAULT_SAMPLE_RATE = 44100


class BGMProcessor:
    """
    背景音乐处理器类

    提供背景音乐的格式验证、音量调节、混音、Ducking等处理功能
    所有音频处理基于FFmpeg命令行工具
    """

    @staticmethod
    def validate_format(filename: str) -> bool:
        """
        验证音频文件格式是否受支持

        Args:
            filename: 文件名(含扩展名)

        Returns:
            bool: 格式是否受支持
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in BGM_ALLOWED_FORMATS

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        验证文件大小是否在允许范围内

        Args:
            file_size: 文件大小(字节)

        Returns:
            bool: 文件大小是否合法
        """
        return 10240 <= file_size <= BGM_MAX_FILE_SIZE

    @staticmethod
    def get_audio_info(file_path: str) -> Optional[dict]:
        """
        获取音频文件信息

        使用ffprobe获取音频时长、采样率、声道数、比特率等信息

        Args:
            file_path: 音频文件路径

        Returns:
            Optional[dict]: 音频信息字典，获取失败返回None
                - duration: 时长(秒)
                - sample_rate: 采样率
                - channels: 声道数
                - bit_rate: 比特率
                - format: 格式
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration,bit_rate:stream=sample_rate,channels,codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
            lines = output.split("\n")

            info = {}
            if len(lines) >= 1:
                try:
                    info["duration"] = float(lines[0])
                except ValueError:
                    info["duration"] = 0
            if len(lines) >= 2:
                try:
                    info["bit_rate"] = int(lines[1])
                except ValueError:
                    info["bit_rate"] = 0
            if len(lines) >= 3:
                try:
                    info["sample_rate"] = int(lines[2])
                except ValueError:
                    info["sample_rate"] = 44100
            if len(lines) >= 4:
                try:
                    info["channels"] = int(lines[3])
                except ValueError:
                    info["channels"] = 2
            if len(lines) >= 5:
                info["format"] = lines[4]

            return info

        except FileNotFoundError:
            app_logger.error("[BGMProcessor] ffprobe未找到，请安装FFmpeg")
            return None
        except Exception as e:
            app_logger.error(f"[BGMProcessor] 获取音频信息失败: {str(e)}")
            return None

    @staticmethod
    def volume_to_db(volume_percent: int) -> float:
        """
        将音量百分比转换为分贝值

        映射公式: dB = 20 × log10(volume / 100)
        0% → -∞ dB (静音), 100% → 0 dB (原始音量)

        Args:
            volume_percent: 音量百分比(0-100)

        Returns:
            float: 分贝值
        """
        if volume_percent <= 0:
            return -60.0
        if volume_percent >= 100:
            return 0.0
        import math
        return 20 * math.log10(volume_percent / 100.0)

    @staticmethod
    def mix_bgm_to_video(
        video_path: str,
        bgm_path: str,
        output_path: str,
        volume: int = 30,
        fade_in: float = 1.0,
        fade_out: float = 1.5,
        loop: bool = True,
        start_offset: float = 0.0
    ) -> str:
        """
        将背景音乐混入视频文件

        使用FFmpeg的amix滤镜实现双轨混音，支持音量调节、淡入淡出、循环播放

        Args:
            video_path: 输入视频文件路径
            bgm_path: 背景音乐文件路径
            output_path: 输出视频文件路径
            volume: 背景音乐音量百分比(0-100)
            fade_in: 淡入时长(秒)
            fade_out: 淡出时长(秒)
            loop: 是否循环播放
            start_offset: 音乐起始偏移(秒)

        Returns:
            str: 输出文件路径

        Raises:
            FileNotFoundError: 输入文件不存在
            subprocess.CalledProcessError: FFmpeg执行失败
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        if not os.path.exists(bgm_path):
            raise FileNotFoundError(f"音乐文件不存在: {bgm_path}")

        volume_factor = volume / 100.0

        video_duration = BGMProcessor._get_video_duration(video_path)

        bgm_filter_parts = []

        if start_offset > 0:
            bgm_filter_parts.append(f"atrim=start={start_offset}")

        if loop:
            bgm_filter_parts.append("aloop=loop=-1:size=2e+09")

        bgm_filter_parts.append(f"volume={volume_factor}")

        if fade_in > 0:
            bgm_filter_parts.append(f"afade=t=in:st=0:d={fade_in}")

        if fade_out > 0 and video_duration > 0:
            fade_out_start = max(0, video_duration - fade_out)
            bgm_filter_parts.append(f"afade=t=out:st={fade_out_start}:d={fade_out}")

        bgm_filter = ",".join(bgm_filter_parts)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]{bgm_filter}[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ]

        app_logger.info(f"[BGMProcessor] 开始混音: volume={volume}%, fade_in={fade_in}s, fade_out={fade_out}s, loop={loop}")
        subprocess.run(cmd, check=True, capture_output=True)
        app_logger.info(f"[BGMProcessor] 混音完成: {output_path}")

        return output_path

    @staticmethod
    def apply_ducking(
        voice_path: str,
        bgm_path: str,
        output_path: str,
        bgm_volume: int = 30,
        duck_threshold_db: float = -30.0,
        duck_amount_db: float = 6.0,
        attack: float = 0.3,
        release: float = 0.5
    ) -> str:
        """
        应用Ducking效果: 当语音活跃时自动降低背景音乐音量

        使用FFmpeg的sidechaincompress滤镜实现语音避让

        Args:
            voice_path: 语音音频文件路径
            bgm_path: 背景音乐文件路径
            output_path: 输出文件路径
            bgm_volume: 背景音乐基础音量百分比
            duck_threshold_db: 语音检测阈值(dB)
            duck_amount_db: 避让时降低的音量(dB)
            attack: 攻击时间(秒)
            release: 释放时间(秒)

        Returns:
            str: 输出文件路径

        Raises:
            FileNotFoundError: 输入文件不存在
            subprocess.CalledProcessError: FFmpeg执行失败
        """
        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"语音文件不存在: {voice_path}")
        if not os.path.exists(bgm_path):
            raise FileNotFoundError(f"音乐文件不存在: {bgm_path}")

        volume_factor = bgm_volume / 100.0

        cmd = [
            "ffmpeg", "-y",
            "-i", voice_path,
            "-i", bgm_path,
            "-filter_complex",
            (
                f"[0:a]aresample=44100,"
                f"highpass=f=200,lowpass=f=3000"
                f"[voice];"
                f"[1:a]aresample=44100,volume={volume_factor},"
                f"aloop=loop=-1:size=2e+09,"
                f"sidechaincompress=threshold={duck_threshold_db}dB:"
                f"ratio=4:attack={attack}:release={release}:makeup={duck_amount_db}dB"
                f"[bgm];"
                f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            ),
            "-map", "[aout]",
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]

        app_logger.info(f"[BGMProcessor] 应用Ducking效果: volume={bgm_volume}%, threshold={duck_threshold_db}dB")
        subprocess.run(cmd, check=True, capture_output=True)
        app_logger.info(f"[BGMProcessor] Ducking处理完成: {output_path}")

        return output_path

    @staticmethod
    def _get_video_duration(video_path: str) -> float:
        """
        获取视频文件时长

        Args:
            video_path: 视频文件路径

        Returns:
            float: 时长(秒)，获取失败返回0
        """
        try:
            cmd = [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ]
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
            return float(output)
        except Exception:
            return 0.0

    @staticmethod
    def generate_thumbnail(video_path: str, output_path: str, time_offset: float = 1.0) -> str:
        """
        从视频生成缩略图

        Args:
            video_path: 视频文件路径
            output_path: 缩略图输出路径
            time_offset: 截取时间点(秒)

        Returns:
            str: 缩略图文件路径

        Raises:
            subprocess.CalledProcessError: FFmpeg执行失败
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(time_offset),
            "-frames:v", "1",
            "-q:v", "2",
            "-s", "320x180",
            output_path
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        app_logger.info(f"[BGMProcessor] 缩略图生成完成: {output_path}")
        return output_path


bgm_processor = BGMProcessor()
