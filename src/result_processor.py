"""
结果处理模块
负责处理OCR结果，生成JSON和HTML输出
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import re

from .config import RESULTS_DIR, TEMPLATES_DIR

logger = logging.getLogger(__name__)


class ResultProcessor:
    """结果处理器"""
    
    def __init__(self):
        self.results_dir = RESULTS_DIR
        self.templates_dir = TEMPLATES_DIR
        
    def create_result_data(self, 
                          image_info: dict, 
                          ocr_result: dict, 
                          process_info: dict = None) -> dict:
        """
        创建完整的结果数据结构
        
        Args:
            image_info: 图像信息
            ocr_result: OCR结果
            process_info: 处理信息
            
        Returns:
            完整的结果数据
        """
        result_data = {
            'metadata': {
                'version': '1.0',
                'created_time': datetime.now().isoformat(),
                'processor': 'OCR2LATEX'
            },
            'image_info': {
                'filename': image_info.get('filename', ''),
                'original_size': image_info.get('size', [0, 0]),
                'file_size': image_info.get('file_size', 0),
                'format': image_info.get('format', ''),
                **(process_info if process_info else {})
            },
            'ocr_result': {
                'success': ocr_result.get('success', False),
                'raw_text': ocr_result.get('raw_text', ''),
                'latex_content': ocr_result.get('latex_content', ''),
                'confidence': ocr_result.get('confidence', 0.0),
                'processing_time': ocr_result.get('processing_time', 0),
                'usage_count': ocr_result.get('usage_count', 0),
                'error': ocr_result.get('error', None)
            },
            'regions': self._process_regions(ocr_result.get('regions', [])),
            'analysis': self._analyze_content(ocr_result)
        }
        
        return result_data
    
    def _process_regions(self, regions: List[dict]) -> List[dict]:
        """
        处理区域信息
        
        Args:
            regions: 原始区域列表
            
        Returns:
            处理后的区域列表
        """
        processed_regions = []
        
        for i, region in enumerate(regions):
            processed_region = {
                'id': i + 1,
                'type': self._classify_region_type(region.get('text', ''), region.get('latex', '')),
                'text': region.get('text', ''),
                'latex': region.get('latex', ''),
                'confidence': region.get('confidence', 0.0),
                'bbox': region.get('bbox', {}),
                'analysis': self._analyze_region(region)
            }
            processed_regions.append(processed_region)
        
        return processed_regions
    
    def _classify_region_type(self, text: str, latex: str) -> str:
        """
        分类区域类型
        
        Args:
            text: 文本内容
            latex: LaTeX内容
            
        Returns:
            区域类型
        """
        # 检查是否包含数学公式
        math_patterns = [
            r'\\frac', r'\\sum', r'\\int', r'\\sqrt', r'\\alpha', r'\\beta',
            r'\^', r'_', r'\\cdot', r'\\times', r'\\div', r'\\pm',
            r'\\leq', r'\\geq', r'\\neq', r'\\approx', r'\\infty'
        ]
        
        if latex and any(re.search(pattern, latex) for pattern in math_patterns):
            return 'formula'
        
        # 检查是否为纯数字
        if text and re.match(r'^[\d\s\.\,\+\-\=]+$', text.strip()):
            return 'number'
        
        # 检查是否包含中文
        if text and re.search(r'[\u4e00-\u9fff]', text):
            return 'chinese_text'
        
        # 检查是否为英文文本
        if text and re.match(r'^[a-zA-Z\s\.\,\!\?\;\:]+$', text.strip()):
            return 'english_text'
        
        return 'mixed'
    
    def _analyze_region(self, region: dict) -> dict:
        """
        分析单个区域
        
        Args:
            region: 区域信息
            
        Returns:
            分析结果
        """
        text = region.get('text', '')
        latex = region.get('latex', '')
        
        analysis = {
            'char_count': len(text),
            'has_chinese': bool(re.search(r'[\u4e00-\u9fff]', text)),
            'has_math': bool(latex and any(symbol in latex for symbol in ['\\', '^', '_', '{', '}'])),
            'complexity': 'simple'
        }
        
        # 判断复杂度
        if latex:
            if len(latex) > 50 or latex.count('\\') > 5:
                analysis['complexity'] = 'complex'
            elif len(latex) > 20 or latex.count('\\') > 2:
                analysis['complexity'] = 'medium'
        
        return analysis
    
    def _analyze_content(self, ocr_result: dict) -> dict:
        """
        分析整体内容
        
        Args:
            ocr_result: OCR结果
            
        Returns:
            内容分析
        """
        text = ocr_result.get('raw_text', '')
        latex = ocr_result.get('latex_content', '')
        regions = ocr_result.get('regions', [])
        
        analysis = {
            'total_chars': len(text),
            'total_regions': len(regions),
            'region_types': {},
            'has_formulas': bool(latex and '\\' in latex),
            'language': 'mixed',
            'complexity_score': 0
        }
        
        # 统计区域类型
        for region in regions:
            region_type = self._classify_region_type(
                region.get('text', ''), 
                region.get('latex', '')
            )
            analysis['region_types'][region_type] = analysis['region_types'].get(region_type, 0) + 1
        
        # 判断主要语言
        if re.search(r'[\u4e00-\u9fff]', text):
            analysis['language'] = 'chinese' if len(re.findall(r'[\u4e00-\u9fff]', text)) > len(text) * 0.3 else 'mixed'
        elif re.match(r'^[a-zA-Z\s\d\.\,\!\?\;\:\+\-\=\(\)]+$', text.strip()):
            analysis['language'] = 'english'
        
        # 计算复杂度分数
        complexity_score = 0
        if latex:
            complexity_score += len(latex) * 0.1
            complexity_score += latex.count('\\') * 2
            complexity_score += latex.count('{') * 1
        complexity_score += len(regions) * 5
        
        analysis['complexity_score'] = min(100, int(complexity_score))
        
        return analysis
    
    def save_json_result(self, result_data: dict, filename: str) -> str:
        """
        保存JSON结果文件
        
        Args:
            result_data: 结果数据
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的文件路径
        """
        try:
            # 生成文件路径
            json_filename = f"{filename}_result.json"
            json_path = self.results_dir / json_filename
            
            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON结果已保存: {json_path}")
            return str(json_path)
            
        except Exception as e:
            logger.error(f"保存JSON结果失败: {e}")
            return ""
    
    def generate_html_result(self, result_data: dict, filename: str) -> str:
        """
        生成HTML结果文件
        
        Args:
            result_data: 结果数据
            filename: 文件名（不含扩展名）
            
        Returns:
            保存的HTML文件路径
        """
        try:
            # 读取HTML模板
            template_path = self.templates_dir / "result_viewer.html"
            
            if not template_path.exists():
                # 如果模板不存在，创建一个简单的模板
                self._create_html_template()
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 替换模板中的占位符
            html_content = template.replace('{{RESULT_DATA}}', json.dumps(result_data, ensure_ascii=False, indent=2))
            html_content = html_content.replace('{{FILENAME}}', result_data['image_info']['filename'])
            
            # 生成HTML文件路径
            html_filename = f"{filename}_result.html"
            html_path = self.results_dir / html_filename
            
            # 保存HTML文件
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML结果已保存: {html_path}")
            return str(html_path)
            
        except Exception as e:
            logger.error(f"生成HTML结果失败: {e}")
            return ""
    
    def _create_html_template(self):
        """创建HTML模板文件"""
        template_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR识别结果 - {{FILENAME}}</title>
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            border: 1px solid #e1e5e9;
            border-radius: 6px;
            background: #fafbfc;
        }
        .section h2 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }
        .info-item {
            background: white;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }
        .info-label {
            font-weight: bold;
            color: #555;
            font-size: 0.9em;
        }
        .info-value {
            margin-top: 5px;
            font-size: 1.1em;
        }
        .text-content {
            background: white;
            padding: 20px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-size: 1.1em;
            line-height: 1.8;
            white-space: pre-wrap;
        }
        .latex-content {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 4px;
            border: 1px solid #e9ecef;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            overflow-x: auto;
        }
        .regions {
            display: grid;
            gap: 15px;
        }
        .region {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
        }
        .region-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .region-type {
            background: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .confidence {
            font-weight: bold;
            color: #27ae60;
        }
        .json-viewer {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        
        @media (max-width: 768px) {
            body { padding: 10px; }
            .header { padding: 20px; }
            .content { padding: 20px; }
            .header h1 { font-size: 2em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 OCR识别结果</h1>
            <p>文件: {{FILENAME}}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 识别概览</h2>
                <div class="info-grid" id="overview"></div>
            </div>
            
            <div class="section">
                <h2>📝 识别文本</h2>
                <div class="text-content" id="recognizedText"></div>
            </div>
            
            <div class="section">
                <h2>🔬 LaTeX内容</h2>
                <div class="latex-content" id="latexContent"></div>
                <h3>渲染效果:</h3>
                <div id="mathPreview" style="font-size: 1.2em; padding: 15px; background: white; border: 1px solid #ddd; border-radius: 4px;"></div>
            </div>
            
            <div class="section">
                <h2>🎯 区域详情</h2>
                <div class="regions" id="regions"></div>
            </div>
            
            <div class="section">
                <h2>🔍 完整数据</h2>
                <div class="json-viewer" id="jsonData"></div>
            </div>
        </div>
    </div>

    <script>
        // 结果数据
        const resultData = {{RESULT_DATA}};
        
        // 渲染概览信息
        function renderOverview() {
            const overview = document.getElementById('overview');
            const data = resultData;
            
            const items = [
                { label: '处理状态', value: data.ocr_result.success ? '✅ 成功' : '❌ 失败', class: data.ocr_result.success ? 'success' : 'error' },
                { label: '置信度', value: (data.ocr_result.confidence * 100).toFixed(1) + '%', class: data.ocr_result.confidence > 0.8 ? 'success' : 'warning' },
                { label: '处理时间', value: data.ocr_result.processing_time.toFixed(2) + '秒' },
                { label: '图像尺寸', value: data.image_info.original_size.join(' × ') },
                { label: '区域数量', value: data.regions.length + '个' },
                { label: '字符数量', value: data.analysis.total_chars + '个' },
                { label: '主要语言', value: data.analysis.language },
                { label: '复杂度', value: data.analysis.complexity_score + '/100' }
            ];
            
            items.forEach(item => {
                const div = document.createElement('div');
                div.className = 'info-item';
                div.innerHTML = `
                    <div class="info-label">${item.label}</div>
                    <div class="info-value ${item.class || ''}">${item.value}</div>
                `;
                overview.appendChild(div);
            });
        }
        
        // 渲染识别文本
        function renderText() {
            const textElement = document.getElementById('recognizedText');
            textElement.textContent = resultData.ocr_result.raw_text || '无识别文本';
        }
        
        // 渲染LaTeX内容
        function renderLatex() {
            const latexElement = document.getElementById('latexContent');
            const previewElement = document.getElementById('mathPreview');
            
            const latexContent = resultData.ocr_result.latex_content || '无LaTeX内容';
            latexElement.textContent = latexContent;
            
            if (latexContent !== '无LaTeX内容') {
                previewElement.innerHTML = '$$' + latexContent + '$$';
                // 重新渲染MathJax
                if (window.MathJax) {
                    MathJax.typesetPromise([previewElement]).catch(function (err) {
                        console.log('MathJax渲染错误:', err);
                        previewElement.innerHTML = '<span class="error">LaTeX渲染失败</span>';
                    });
                }
            } else {
                previewElement.innerHTML = '<span class="warning">无数学公式内容</span>';
            }
        }
        
        // 渲染区域信息
        function renderRegions() {
            const regionsElement = document.getElementById('regions');
            
            if (resultData.regions.length === 0) {
                regionsElement.innerHTML = '<p>无区域信息</p>';
                return;
            }
            
            resultData.regions.forEach(region => {
                const div = document.createElement('div');
                div.className = 'region';
                div.innerHTML = `
                    <div class="region-header">
                        <span class="region-type">${region.type}</span>
                        <span class="confidence">置信度: ${(region.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div><strong>文本:</strong> ${region.text || '无'}</div>
                    <div><strong>LaTeX:</strong> <code>${region.latex || '无'}</code></div>
                `;
                regionsElement.appendChild(div);
            });
        }
        
        // 渲染JSON数据
        function renderJson() {
            const jsonElement = document.getElementById('jsonData');
            jsonElement.textContent = JSON.stringify(resultData, null, 2);
        }
        
        // 初始化页面
        document.addEventListener('DOMContentLoaded', function() {
            renderOverview();
            renderText();
            renderLatex();
            renderRegions();
            renderJson();
        });
        
        // MathJax配置
        window.MathJax = {
            tex: {
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            },
            svg: {
                fontCache: 'global'
            }
        };
    </script>
</body>
</html>'''
        
        template_path = self.templates_dir / "result_viewer.html"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        logger.info(f"HTML模板已创建: {template_path}")
    
    def process_and_save_results(self, 
                               image_info: dict, 
                               ocr_result: dict, 
                               process_info: dict = None,
                               base_filename: str = None) -> dict:
        """
        处理并保存所有结果
        
        Args:
            image_info: 图像信息
            ocr_result: OCR结果
            process_info: 处理信息
            base_filename: 基础文件名
            
        Returns:
            保存结果信息
        """
        try:
            # 生成基础文件名
            if not base_filename:
                filename = image_info.get('filename', 'unknown')
                base_filename = Path(filename).stem
            
            # 创建结果数据
            result_data = self.create_result_data(image_info, ocr_result, process_info)
            
            # 保存JSON文件
            json_path = self.save_json_result(result_data, base_filename)
            
            # 生成HTML文件
            html_path = self.generate_html_result(result_data, base_filename)
            
            return {
                'success': True,
                'json_path': json_path,
                'html_path': html_path,
                'result_data': result_data
            }
            
        except Exception as e:
            logger.error(f"处理和保存结果失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'json_path': '',
                'html_path': '',
                'result_data': {}
            }


# 创建全局实例
result_processor = ResultProcessor()
