"""
阿里云字幕生成和智能剪辑API使用示例

本文件提供完整的API调用流程示例，包括：
1. 字幕生成API使用示例
2. 智能剪辑API使用示例
3. 完整的故事视频生成流程示例
"""

import asyncio
from typing import List

# ============================================
# 一、字幕生成API使用示例
# ============================================

async def subtitle_example():
    """
    字幕生成API完整使用示例

    功能：为故事视频自动生成精准匹配的字幕内容
    支持：SRT、ASS、VTT、JSON格式导出
    """
    from app.services.subtitle_service import (
        subtitle_service,
        SubtitleFormat,
        SubtitleStatus
    )

    # 1. 配置说明（在.env文件中配置）
    # ALIYUN_ACCESS_KEY_ID=your-access-key-id
    # ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
    # ALIYUN_SUBTITLE_APP_KEY=your-subtitle-app-key

    # 2. 视频文件URL（支持mp3/wav/m4a/mp4等格式）
    video_url = "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/story_001.mp4"

    # 3. 提交字幕生成任务
    print("提交字幕生成任务...")
    submit_result = await subtitle_service.submit_file_task(
        audio_url=video_url,
        language="zh-CN",
        enable_words=True,
        enable_punctuation=True
    )

    if submit_result.status == SubtitleStatus.FAILED:
        print(f"任务提交失败: {submit_result.error_message}")
        return

    task_id = submit_result.task_id
    print(f"任务已提交，任务ID: {task_id}")

    # 4. 轮询查询任务状态
    print("等待字幕生成完成...")
    while True:
        await asyncio.sleep(3)
        result = await subtitle_service.query_task_status(task_id)

        if result.status == SubtitleStatus.COMPLETED:
            print(f"字幕生成完成，共 {len(result.segments)} 条字幕")
            break
        elif result.status == SubtitleStatus.FAILED:
            print(f"字幕生成失败: {result.error_message}")
            return

    # 5. 导出SRT格式字幕
    srt_content = subtitle_service.export_subtitle(
        result,
        format=SubtitleFormat.SRT,
        output_path="/output/subtitle.srt"
    )
    print("SRT字幕已保存到 /output/subtitle.srt")

    # 6. 导出ASS格式字幕（支持样式）
    ass_content = subtitle_service.export_subtitle(
        result,
        format=SubtitleFormat.ASS,
        output_path="/output/subtitle.ass"
    )
    print("ASS字幕已保存到 /output/subtitle.ass")

    # 7. 一键生成字幕（完整流程）
    print("\n使用一键生成方法...")
    result = await subtitle_service.generate_subtitle_from_video(
        video_url=video_url,
        format=SubtitleFormat.SRT,
        language="zh-CN",
        output_path="/output/auto_subtitle.srt",
        max_wait_seconds=300
    )

    if result.status == SubtitleStatus.COMPLETED:
        print(f"一键生成完成，时长: {result.duration}ms")


# ============================================
# 二、智能剪辑API使用示例
# ============================================

async def edit_example():
    """
    智能剪辑API完整使用示例

    功能：将多段分镜视频素材智能拼接为完整故事片
    支持：转场效果、滤镜、背景音乐处理
    """
    from app.services.edit_service import (
        edit_service,
        VideoClip,
        BackgroundMusic,
        EditTimeline,
        TransitionType,
        FilterType,
        EditTaskStatus
    )

    # 1. 配置说明（在.env文件中配置）
    # ALIYUN_ACCESS_KEY_ID=your-access-key-id
    # ALIYUN_ACCESS_KEY_SECRET=your-access-key-secret
    # ALIYUN_EDIT_REGION=cn-shanghai
    # ALIYUN_EDIT_OUTPUT_BUCKET=your-output-bucket

    # 2. 准备视频片段列表
    video_urls = [
        "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/clip_001.mp4",
        "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/clip_002.mp4",
        "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/clip_003.mp4",
        "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/clip_004.mp4",
        "https://your-bucket.oss-cn-shanghai.aliyuncs.com/videos/clip_005.mp4"
    ]

    # 3. 获取可用的转场效果列表
    transitions = edit_service.get_available_transitions()
    print("可用转场效果:")
    for t in transitions:
        print(f"  - {t['type']}: {t['name']}")

    # 4. 获取可用的滤镜效果列表
    filters = edit_service.get_available_filters()
    print("\n可用滤镜效果:")
    for f in filters:
        print(f"  - {f['type']}: {f['name']}")

    # 5. 简单合并视频（便捷方法）
    print("\n使用便捷方法合并视频...")
    result = await edit_service.merge_videos(
        video_urls=video_urls,
        output_bucket="your-output-bucket",
        output_object="story/final_video.mp4",
        transition=TransitionType.DISSOLVE,
        transition_duration=0.5,
        filter_type=FilterType.WARM,
        bgm_url="https://your-bucket.oss-cn-shanghai.aliyuncs.com/bgm/story_bgm.mp3",
        bgm_volume=30,
        bgm_fade_in=1.0,
        bgm_fade_out=1.5,
        resolution="1920x1080",
        fps=30
    )

    if result.status == EditTaskStatus.FAILED:
        print(f"合并失败: {result.error_message}")
        return

    print(f"任务已提交，任务ID: {result.task_id}")

    # 6. 完全控制的剪辑方式
    print("\n使用完全控制方式剪辑...")

    # 创建视频片段配置
    clips = []
    for idx, url in enumerate(video_urls):
        clip = VideoClip(
            video_url=url,
            start_time=0.0,
            end_time=0.0,
            duration=5.0,
            transition_in=TransitionType.FADE if idx == 0 else TransitionType.DISSOLVE,
            transition_out=TransitionType.FADE if idx == len(video_urls) - 1 else TransitionType.DISSOLVE,
            transition_duration=0.5,
            filter_type=FilterType.WARM,
            volume=100
        )
        clips.append(clip)

    # 创建背景音乐配置
    bgm = BackgroundMusic(
        music_url="https://your-bucket.oss-cn-shanghai.aliyuncs.com/bgm/story_bgm.mp3",
        volume=30,
        fade_in=1.0,
        fade_out=1.5,
        loop=True,
        start_time=0.0
    )

    # 创建时间线配置
    timeline = EditTimeline(
        clips=clips,
        bgm=bgm,
        total_duration=25.0,
        resolution="1920x1080",
        fps=30
    )

    # 提交剪辑任务并等待完成
    result = await edit_service.edit_with_full_control(
        timeline=timeline,
        output_bucket="your-output-bucket",
        output_object="story/final_video_full.mp4",
        max_wait_seconds=600
    )

    if result.status == EditTaskStatus.COMPLETED:
        print(f"剪辑完成！")
        print(f"  输出URL: {result.output_url}")
        print(f"  时长: {result.duration}秒")
        print(f"  分辨率: {result.resolution}")
        print(f"  帧率: {result.fps}fps")
        print(f"  文件大小: {result.file_size}字节")
    else:
        print(f"剪辑失败: {result.error_message}")


# ============================================
# 三、完整故事视频生成流程示例
# ============================================

async def complete_story_video_workflow():
    """
    完整的故事视频生成流程示例

    流程：
    1. 生成各分镜视频（AI视频生成）
    2. 生成字幕（字幕生成API）
    3. 智能剪辑合成（智能剪辑API）
    """
    from app.services.aliyun_provider import aliyun_provider
    from app.services.subtitle_service import subtitle_service, SubtitleFormat
    from app.services.edit_service import edit_service, TransitionType, FilterType

    print("=" * 50)
    print("完整故事视频生成流程")
    print("=" * 50)

    # 步骤1：生成各分镜视频
    print("\n步骤1：生成分镜视频...")
    story_segments = [
        {
            "image_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/images/scene_001.jpg",
            "prompt": "A little girl walking into a magical forest, warm sunlight"
        },
        {
            "image_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/images/scene_002.jpg",
            "prompt": "The girl meets a friendly rabbit in the forest"
        },
        {
            "image_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/images/scene_003.jpg",
            "prompt": "They discover a hidden treasure chest together"
        }
    ]

    video_urls = []
    for idx, segment in enumerate(story_segments):
        print(f"  生成第 {idx + 1} 段视频...")
        result = await aliyun_provider.generate_video(
            image_url=segment["image_url"],
            prompt=segment["prompt"],
            duration=5
        )
        # 实际应用中需要轮询等待完成并获取视频URL
        # video_urls.append(completed_video_url)
        print(f"    任务ID: {result.task_id}")

    # 步骤2：生成字幕
    print("\n步骤2：生成字幕...")
    # 假设第一个视频有音频
    subtitle_result = await subtitle_service.generate_subtitle_from_video(
        video_url=video_urls[0] if video_urls else "https://example.com/video.mp4",
        format=SubtitleFormat.SRT,
        language="zh-CN",
        output_path="/output/story_subtitle.srt"
    )
    print(f"  字幕生成完成，共 {len(subtitle_result.segments)} 条")

    # 步骤3：智能剪辑合成
    print("\n步骤3：智能剪辑合成...")
    edit_result = await edit_service.merge_videos(
        video_urls=video_urls if video_urls else ["https://example.com/clip1.mp4"],
        output_bucket="your-output-bucket",
        output_object="story/final_story.mp4",
        transition=TransitionType.DISSOLVE,
        filter_type=FilterType.WARM,
        bgm_url="https://your-bucket.oss-cn-shanghai.aliyuncs.com/bgm/story_bgm.mp3",
        bgm_volume=30
    )
    print(f"  剪辑任务已提交: {edit_result.task_id}")

    print("\n" + "=" * 50)
    print("流程完成！")
    print("=" * 50)


# ============================================
# 四、错误处理示例
# ============================================

async def error_handling_example():
    """
    错误处理机制示例
    """
    from app.services.subtitle_service import subtitle_service, SubtitleStatus
    from app.services.edit_service import edit_service, EditTaskStatus

    print("错误处理示例")

    # 1. 配置错误检查
    try:
        result = await subtitle_service.submit_file_task(
            audio_url="https://invalid-url.mp4"
        )
        if result.status == SubtitleStatus.FAILED:
            print(f"任务失败: {result.error_message}")
    except Exception as e:
        print(f"异常捕获: {str(e)}")

    # 2. 任务超时处理
    result = await subtitle_service.generate_subtitle_from_video(
        video_url="https://example.com/long_video.mp4",
        max_wait_seconds=10
    )
    if result.status == SubtitleStatus.FAILED:
        if "超时" in result.error_message:
            print("任务超时，可以稍后重试或使用异步回调")

    # 3. 重试机制示例
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await edit_service.merge_videos(
                video_urls=["https://example.com/clip.mp4"],
                output_bucket="bucket",
                output_object="output.mp4"
            )
            if result.status != EditTaskStatus.FAILED:
                break
            print(f"第 {attempt + 1} 次尝试失败")
        except Exception as e:
            print(f"第 {attempt + 1} 次异常: {str(e)}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5)


# ============================================
# 主函数
# ============================================

async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("阿里云字幕生成和智能剪辑API使用示例")
    print("=" * 60)

    # 运行字幕生成示例
    print("\n>>> 字幕生成示例 <<<")
    await subtitle_example()

    # 运行智能剪辑示例
    print("\n>>> 智能剪辑示例 <<<")
    await edit_example()

    # 运行完整流程示例
    print("\n>>> 完整流程示例 <<<")
    await complete_story_video_workflow()

    # 运行错误处理示例
    print("\n>>> 错误处理示例 <<<")
    await error_handling_example()


if __name__ == "__main__":
    asyncio.run(main())
