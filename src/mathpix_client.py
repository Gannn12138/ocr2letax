"""
Mathpix API客户端
负责与Mathpix OCR服务进行通信
"""

import requests
import json
import time
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import base64

from .config import (
    MATHPIX_APP_ID, 
    MATHPIX_APP_KEY, 
    MATHPIX_API_URL,
    MAX_RETRIES,
    TIMEOUT,
    OCR_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class MathpixClient:
    """Mathpix API客户端"""
    
    def __init__(self, app_id: str = None, app_key: str = None):
        self.app_id = app_id or MATHPIX_APP_ID
        self.app_key = app_key or MATHPIX_APP_KEY
        self.api_url = MATHPIX_API_URL
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'app_id': self.app_id,
            'app_key': self.app_key,
            'Content-type': 'application/json'
        })
        
        # API使用统计
        self.usage_count = 0
        self.last_request_time = None
        
    def check_credentials(self) -> bool:
        """
        检查API凭证是否有效
        
        Returns:
            凭证是否有效
        """
        if not self.app_id or self.app_id == "your_app_id_here":
            logger.error("Mathpix APP ID未设置")
            return False
            
        if not self.app_key or self.app_key == "your_app_key_here":
            logger.error("Mathpix APP KEY未设置")
            return False
            
        return True
    
    def _make_request(self, data: dict, retries: int = MAX_RETRIES) -> Optional[dict]:
        """
        发送API请求
        
        Args:
            data: 请求数据
            retries: 重试次数
            
        Returns:
            API响应数据
        """
        for attempt in range(retries):
            try:
                # 记录请求时间
                self.last_request_time = datetime.now()
                
                # 发送请求
                response = self.session.post(
                    self.api_url,
                    json=data,
                    timeout=TIMEOUT
                )
                
                # 更新使用计数
                self.usage_count += 1
                
                # 检查响应状态
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"API请求成功，使用次数: {self.usage_count}")
                    return result
                    
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    wait_time = 2 ** attempt
                    logger.warning(f"API速率限制，等待 {wait_time} 秒后重试")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 401:
                    logger.error("API认证失败，请检查APP ID和APP KEY")
                    return None
                    
                elif response.status_code == 402:
                    logger.error("API配额已用完")
                    return None
                    
                else:
                    logger.error(f"API请求失败，状态码: {response.status_code}")
                    logger.error(f"响应内容: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时，重试 {attempt + 1}/{retries}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"请求异常: {e}")
                
            # 等待后重试
            if attempt < retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        
        logger.error("API请求失败，已达到最大重试次数")
        return None
    
    def ocr_image(self, image_base64: str, options: dict = None) -> Optional[dict]:
        """
        对图像进行OCR识别
        
        Args:
            image_base64: base64编码的图像
            options: OCR选项
            
        Returns:
            OCR结果
        """
        if not self.check_credentials():
            return None
            
        # 默认选项
        default_options = {
            'formats': ['text', 'latex_styled'],
            'data_options': {
                'include_asciimath': True,
                'include_latex': True
            }
        }
        
        if options:
            default_options.update(options)
        
        # 构建请求数据
        request_data = {
            'src': f"data:image/jpeg;base64,{image_base64}",
            **default_options
        }
        
        logger.info("开始OCR识别...")
        start_time = time.time()
        
        # 发送请求
        result = self._make_request(request_data)
        
        if result:
            processing_time = time.time() - start_time
            logger.info(f"OCR识别完成，耗时: {processing_time:.2f}秒")
            
            # 添加处理时间到结果中
            result['processing_time'] = processing_time
            result['usage_count'] = self.usage_count
            
        return result
    
    def parse_ocr_result(self, ocr_result: dict) -> dict:
        """
        解析OCR结果
        
        Args:
            ocr_result: 原始OCR结果
            
        Returns:
            解析后的结果
        """
        try:
            parsed_result = {
                'success': False,
                'raw_text': '',
                'latex_content': '',
                'confidence': 0.0,
                'regions': [],
                'processing_time': ocr_result.get('processing_time', 0),
                'usage_count': ocr_result.get('usage_count', 0),
                'error': None
            }
            
            # 检查是否有错误
            if 'error' in ocr_result:
                parsed_result['error'] = ocr_result['error']
                return parsed_result
            
            # 提取文本内容
            if 'text' in ocr_result:
                parsed_result['raw_text'] = ocr_result['text']
                parsed_result['success'] = True
            
            # 提取LaTeX内容
            if 'latex_styled' in ocr_result:
                parsed_result['latex_content'] = ocr_result['latex_styled']
            
            # 提取置信度
            if 'confidence' in ocr_result:
                parsed_result['confidence'] = ocr_result['confidence']
            elif 'confidence_rate' in ocr_result:
                parsed_result['confidence'] = ocr_result['confidence_rate']
            
            # 提取区域信息
            if 'detection_list' in ocr_result:
                regions = []
                for detection in ocr_result['detection_list']:
                    region = {
                        'text': detection.get('text', ''),
                        'latex': detection.get('latex', ''),
                        'confidence': detection.get('confidence', 0),
                        'bbox': detection.get('bounding_box', {})
                    }
                    regions.append(region)
                parsed_result['regions'] = regions
            
            # 检查置信度阈值
            if parsed_result['confidence'] < OCR_CONFIDENCE_THRESHOLD:
                logger.warning(f"识别置信度较低: {parsed_result['confidence']:.2f}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"解析OCR结果失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_text': '',
                'latex_content': '',
                'confidence': 0.0,
                'regions': [],
                'processing_time': 0,
                'usage_count': self.usage_count
            }
    
    def process_image(self, image_base64: str, options: dict = None) -> dict:
        """
        完整的图像处理流程
        
        Args:
            image_base64: base64编码的图像
            options: 处理选项
            
        Returns:
            处理结果
        """
        # 执行OCR
        ocr_result = self.ocr_image(image_base64, options)
        
        if ocr_result is None:
            return {
                'success': False,
                'error': 'OCR请求失败',
                'raw_text': '',
                'latex_content': '',
                'confidence': 0.0,
                'regions': [],
                'processing_time': 0,
                'usage_count': self.usage_count
            }
        
        # 解析结果
        parsed_result = self.parse_ocr_result(ocr_result)
        
        return parsed_result
    
    def get_usage_info(self) -> dict:
        """
        获取API使用信息
        
        Returns:
            使用信息
        """
        return {
            'usage_count': self.usage_count,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'monthly_limit': 1000,  # Mathpix免费版限制
            'remaining': max(0, 1000 - self.usage_count)
        }


# 创建全局实例
mathpix_client = MathpixClient()

