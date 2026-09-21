"""视频处理服务 - 尾帧提取 + 视频拼接"""
from pathlib import Path
from typing import List

import cv2
from moviepy.editor import VideoFileClip, concatenate_videoclips

from app.core.config import settings


class VideoService:
    @staticmethod
    def extract_tail_frame(video_path: str, output_path: str) -> str:
        """提取视频最后一帧并保存为JPEG"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames - 1))
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise ValueError("无法读取视频帧")

        cv2.imwrite(output_path, frame)
        return output_path

    @staticmethod
    def merge_videos(video_paths: List[str], output_path: str) -> str:
        """拼接多个视频文件"""
        if not video_paths:
            raise ValueError("没有可拼接的视频")

        clips = []
        try:
            for path in video_paths:
                if Path(path).exists():
                    clip = VideoFileClip(path)
                    clips.append(clip)

            if not clips:
                raise ValueError("所有视频文件都不存在")

            final = concatenate_videoclips(clips, method="compose")
            final.write_videofile(output_path, codec="libx264", audio_codec="aac")
            final.close()
        finally:
            for clip in clips:
                try:
                    clip.close()
                except Exception:
                    pass

        return output_path

    @staticmethod
    def download_video(url: str, output_path: str) -> str:
        """下载视频到本地"""
        import urllib.request
        urllib.request.urlretrieve(url, output_path)
        return output_path
