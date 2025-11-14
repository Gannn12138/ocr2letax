"""
图像预处理模块
负责图像的加载、预处理、优化等功能
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import logging
from pathlib import Path
from typing import Tuple, Optional
import base64
import io

from .config import MAX_IMAGE_SIZE, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图像处理器"""
    
    def __init__(self):
        self.max_size = MAX_IMAGE_SIZE
        
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            numpy数组格式的图像，如果加载失败返回None
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.error(f"图像文件不存在: {image_path}")
                return None
                
            if path.suffix.lower() not in SUPPORTED_FORMATS:
                logger.error(f"不支持的图像格式: {path.suffix}")
                return None
                
            # 使用PIL加载图像
            with Image.open(image_path) as img:
                # 转换为RGB格式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 转换为numpy数组
                image_array = np.array(img)
                
            logger.info(f"成功加载图像: {image_path}, 尺寸: {image_array.shape}")
            return image_array
            
        except Exception as e:
            logger.error(f"加载图像失败: {e}")
            return None
    
    def resize_image(self, image: np.ndarray, max_size: Tuple[int, int] = None) -> np.ndarray:
        """
        调整图像尺寸
        
        Args:
            image: 输入图像
            max_size: 最大尺寸 (width, height)
            
        Returns:
            调整后的图像
        """
        if max_size is None:
            max_size = self.max_size
            
        h, w = image.shape[:2]
        max_w, max_h = max_size
        
        # 如果图像已经小于最大尺寸，直接返回
        if w <= max_w and h <= max_h:
            return image
            
        # 计算缩放比例
        scale = min(max_w / w, max_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 使用高质量插值进行缩放
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        logger.info(f"图像尺寸调整: {w}x{h} -> {new_w}x{new_h}")
        return resized
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像增强处理
        
        Args:
            image: 输入图像
            
        Returns:
            增强后的图像
        """
        try:
            # 转换为PIL图像进行增强
            pil_image = Image.fromarray(image)
            
            # 对比度增强
            enhancer = ImageEnhance.Contrast(pil_image)
            enhanced = enhancer.enhance(1.2)
            
            # 锐度增强
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.1)
            
            # 转换回numpy数组
            enhanced_array = np.array(enhanced)
            
            logger.info("图像增强处理完成")
            return enhanced_array
            
        except Exception as e:
            logger.error(f"图像增强失败: {e}")
            return image
    
    def correct_skew(self, image: np.ndarray) -> np.ndarray:
        """
        倾斜校正
        
        Args:
            image: 输入图像
            
        Returns:
            校正后的图像
        """
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 霍夫变换检测直线
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is None:
                return image
                
            # 计算倾斜角度
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = theta * 180 / np.pi - 90
                if abs(angle) < 45:  # 只考虑小角度倾斜
                    angles.append(angle)
            
            if not angles:
                return image
                
            # 使用中位数角度进行校正
            median_angle = np.median(angles)
            
            if abs(median_angle) > 0.5:  # 只有角度大于0.5度才进行校正
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                
                # 创建旋转矩阵
                rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                
                # 应用旋转
                corrected = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                         flags=cv2.INTER_CUBIC, 
                                         borderMode=cv2.BORDER_REPLICATE)
                
                logger.info(f"倾斜校正完成，角度: {median_angle:.2f}度")
                return corrected
            
            return image
            
        except Exception as e:
            logger.error(f"倾斜校正失败: {e}")
            return image
    
    def denoise_image(self, image: np.ndarray) -> np.ndarray:
        """
        图像去噪
        
        Args:
            image: 输入图像
            
        Returns:
            去噪后的图像
        """
        try:
            # 使用非局部均值去噪
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
            
            logger.info("图像去噪处理完成")
            return denoised
            
        except Exception as e:
            logger.error(f"图像去噪失败: {e}")
            return image
    
    def preprocess_image(self, image_path: str) -> Optional[Tuple[np.ndarray, dict]]:
        """
        完整的图像预处理流程
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            处理后的图像和处理信息
        """
        # 加载图像
        image = self.load_image(image_path)
        if image is None:
            return None
            
        original_shape = image.shape
        
        # 调整尺寸
        image = self.resize_image(image)
        
        # 图像增强
        image = self.enhance_image(image)
        
        # 倾斜校正
        image = self.correct_skew(image)
        
        # 去噪处理
        image = self.denoise_image(image)
        
        # 处理信息
        process_info = {
            'original_size': original_shape[:2][::-1],  # (width, height)
            'processed_size': image.shape[:2][::-1],
            'preprocessing_steps': ['resize', 'enhance', 'skew_correction', 'denoise']
        }
        
        logger.info("图像预处理完成")
        return image, process_info
    
    def image_to_base64(self, image: np.ndarray, format: str = 'PNG') -> str:
        """
        将图像转换为base64编码
        
        Args:
            image: numpy数组格式的图像
            format: 图像格式
            
        Returns:
            base64编码的图像字符串
        """
        try:
            # 转换为PIL图像
            pil_image = Image.fromarray(image)
            
            # 转换为字节流
            buffer = io.BytesIO()
            pil_image.save(buffer, format=format)
            
            # 编码为base64
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return image_base64
            
        except Exception as e:
            logger.error(f"图像base64编码失败: {e}")
            return ""
    
    def get_image_info(self, image_path: str) -> dict:
        """
        获取图像基本信息
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            图像信息字典
        """
        try:
            path = Path(image_path)
            
            with Image.open(image_path) as img:
                info = {
                    'filename': path.name,
                    'size': img.size,  # (width, height)
                    'mode': img.mode,
                    'format': img.format,
                    'file_size': path.stat().st_size
                }
                
            return info
            
        except Exception as e:
            logger.error(f"获取图像信息失败: {e}")
            return {}


# 创建全局实例
image_processor = ImageProcessor()

